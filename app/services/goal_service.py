"""
Servicio de metas financieras
"""
from typing import List, Dict
from datetime import datetime, date
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.goal import Goal, GoalContribution, GoalType
from app.schemas.goal import GoalCreate, GoalUpdate, GoalContributionCreate
from app.utils.calculations import calculate_goal_progress, project_goal_completion
from dateutil.relativedelta import relativedelta


class GoalService:
    """Servicio para gestión de metas"""
    
    @staticmethod
    def create_goal(db: Session, user_id: int, goal_data: GoalCreate) -> Goal:
        """Crear meta"""
        # Validar que monto inicial no sea mayor que objetivo
        if goal_data.initial_amount > goal_data.target_amount:
            raise HTTPException(
                status_code=400,
                detail="El monto inicial no puede ser mayor que el objetivo"
            )
        
        goal = Goal(
            user_id=user_id,
            name=goal_data.name,
            description=goal_data.description,
            type=goal_data.type,
            target_amount=goal_data.target_amount,
            initial_amount=goal_data.initial_amount,
            current_amount=goal_data.initial_amount,
            target_date=goal_data.target_date,
            linked_account_id=goal_data.linked_account_id,
            auto_contribution_amount=goal_data.auto_contribution_amount,
            auto_contribution_frequency=goal_data.auto_contribution_frequency,
            priority=goal_data.priority,
            color=goal_data.color,
            icon=goal_data.icon,
        )
        
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        return goal
    
    @staticmethod
    def get_goal_with_calculations(db: Session, user_id: int, goal_id: int) -> Dict:
        """Obtener meta con cálculos y proyecciones"""
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Meta no encontrada")
        
        # Calcular progreso
        progress = calculate_goal_progress(goal.current_amount, goal.target_amount)
        remaining = goal.target_amount - goal.current_amount
        
        # Calcular aportación promedio de últimos 3 meses
        three_months_ago = datetime.now() - relativedelta(months=3)
        recent_contributions = db.query(GoalContribution).filter(
            GoalContribution.goal_id == goal_id,
            GoalContribution.date >= three_months_ago
        ).all()
        
        if recent_contributions:
            total_contributed = sum(c.amount for c in recent_contributions)
            avg_monthly = total_contributed / 3
        else:
            avg_monthly = goal.auto_contribution_amount or 0
        
        # Proyectar fecha de completación
        estimated_months = None
        estimated_date = None
        
        if avg_monthly > 0 and remaining > 0:
            estimated_months = project_goal_completion(
                goal.current_amount,
                goal.target_amount,
                avg_monthly
            )
            
            if estimated_months > 0:
                estimated_date = date.today() + relativedelta(months=estimated_months)
        
        # Calcular contribución requerida para cumplir fecha objetivo
        required_monthly = None
        if goal.target_date and remaining > 0:
            months_until_target = (goal.target_date - date.today()).days / 30
            if months_until_target > 0:
                required_monthly = remaining / months_until_target
        
        return {
            "goal": goal,
            "progress_percentage": progress,
            "remaining_amount": remaining,
            "average_monthly_contribution": avg_monthly,
            "estimated_completion_months": estimated_months,
            "estimated_completion_date": estimated_date,
            "required_monthly_contribution": required_monthly,
            "on_track": GoalService._is_on_track(goal, avg_monthly, remaining),
        }
    
    @staticmethod
    def _is_on_track(goal: Goal, avg_monthly: float, remaining: float) -> bool:
        """Determinar si la meta va por buen camino"""
        if not goal.target_date or remaining <= 0:
            return True
        
        months_remaining = (goal.target_date - date.today()).days / 30
        if months_remaining <= 0:
            return False
        
        required_monthly = remaining / months_remaining
        return avg_monthly >= required_monthly
    
    @staticmethod
    def add_contribution(db: Session, user_id: int, 
                        contribution_data: GoalContributionCreate) -> GoalContribution:
        """Agregar contribución a meta"""
        goal = db.query(Goal).filter(
            Goal.id == contribution_data.goal_id,
            Goal.user_id == user_id
        ).first()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Meta no encontrada")
        
        if goal.is_completed:
            raise HTTPException(status_code=400, detail="La meta ya está completada")
        
        # Crear contribución
        contribution = GoalContribution(
            goal_id=contribution_data.goal_id,
            amount=contribution_data.amount,
            date=contribution_data.date,
            notes=contribution_data.notes,
            is_automatic=contribution_data.is_automatic,
        )
        
        db.add(contribution)
        
        # Actualizar monto actual de la meta
        goal.current_amount += contribution_data.amount
        
        # Verificar si se completó
        if goal.current_amount >= goal.target_amount:
            goal.is_completed = True
            goal.completed_at = datetime.now()
        
        db.commit()
        db.refresh(contribution)
        
        return contribution
    
    @staticmethod
    def withdraw_from_goal(db: Session, user_id: int, goal_id: int, 
                          amount: float, notes: str = None) -> Goal:
        """Retirar dinero de una meta"""
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == user_id
        ).first()
        
        if not goal:
            raise HTTPException(status_code=404, detail="Meta no encontrada")
        
        if amount > goal.current_amount:
            raise HTTPException(
                status_code=400,
                detail="No se puede retirar más de lo acumulado"
            )
        
        # Registrar como contribución negativa
        contribution = GoalContribution(
            goal_id=goal_id,
            amount=-amount,
            date=datetime.now(),
            notes=notes or "Retiro",
            is_automatic=False,
        )
        
        db.add(contribution)
        
        # Actualizar monto
        goal.current_amount -= amount
        
        # Si estaba completada y ahora no, desmarcar
        if goal.is_completed and goal.current_amount < goal.target_amount:
            goal.is_completed = False
            goal.completed_at = None
        
        db.commit()
        db.refresh(goal)
        
        return goal
    
    @staticmethod
    def get_available_for_spending(db: Session, user_id: int, 
                                   total_liquid: float) -> float:
        """
        Calcular saldo disponible real para gastar
        (Total líquido - Dinero apartado en metas)
        """
        active_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.is_completed == False,
            Goal.is_archived == False
        ).all()
        
        total_allocated = sum(g.current_amount for g in active_goals)
        
        return total_liquid - total_allocated

