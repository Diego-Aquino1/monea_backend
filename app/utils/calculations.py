"""
Utilidades de cálculos financieros
"""
from datetime import datetime, date, timedelta
from typing import List, Tuple
from dateutil.relativedelta import relativedelta


def calculate_account_balance(initial_balance: float, incomes: float, expenses: float, 
                              transfers_in: float, transfers_out: float) -> float:
    """
    Calcular saldo actual de una cuenta
    Saldo = Saldo Inicial + Ingresos - Gastos + Traspasos Entrantes - Traspasos Salientes
    """
    return initial_balance + incomes - expenses + transfers_in - transfers_out


def calculate_net_worth(assets: float, liabilities: float) -> float:
    """
    Calcular valor neto
    Valor Neto = Activos - Pasivos
    """
    return assets - liabilities


def calculate_credit_available(credit_limit: float, balance_at_cutoff: float, 
                               post_cutoff_balance: float, installment_debt: float) -> float:
    """
    Calcular crédito disponible en tarjeta
    Disponible = Límite - Saldo al Corte - Post-Corte - Deuda MSI
    """
    return credit_limit - balance_at_cutoff - post_cutoff_balance - installment_debt


def calculate_minimum_payment(balance: float, percentage: float) -> float:
    """Calcular pago mínimo de tarjeta"""
    return balance * (percentage / 100.0)


def calculate_interest(balance: float, annual_rate: float, days: int = 30) -> float:
    """
    Calcular interés generado
    Interés = Balance × (Tasa Anual / 365) × Días
    """
    daily_rate = annual_rate / 365.0 / 100.0
    return balance * daily_rate * days


def get_next_cutoff_date(cutoff_day: int, reference_date: date = None) -> date:
    """Obtener próxima fecha de corte"""
    if reference_date is None:
        reference_date = date.today()
    
    # Si el día de corte ya pasó este mes, usar el próximo mes
    try:
        next_cutoff = date(reference_date.year, reference_date.month, cutoff_day)
        if next_cutoff <= reference_date:
            next_cutoff = next_cutoff + relativedelta(months=1)
    except ValueError:
        # Si el día no existe en el mes (ej: 31 en febrero), usar último día del mes
        next_cutoff = date(reference_date.year, reference_date.month + 1, 1) - timedelta(days=1)
    
    return next_cutoff


def get_period_dates(cutoff_day: int, reference_date: date = None) -> Tuple[date, date]:
    """
    Obtener fechas de inicio y fin del periodo actual de tarjeta
    Returns: (fecha_inicio, fecha_corte)
    """
    if reference_date is None:
        reference_date = date.today()
    
    # Fecha de corte de este mes
    try:
        current_cutoff = date(reference_date.year, reference_date.month, cutoff_day)
    except ValueError:
        # Último día del mes si el día no existe
        current_cutoff = date(reference_date.year, reference_date.month + 1, 1) - timedelta(days=1)
    
    if reference_date > current_cutoff:
        # Ya pasó el corte, periodo actual va del corte al próximo corte
        start_date = current_cutoff
        end_date = get_next_cutoff_date(cutoff_day, current_cutoff)
    else:
        # Aún no pasa el corte, periodo va del corte anterior al corte actual
        end_date = current_cutoff
        start_date = get_next_cutoff_date(cutoff_day, current_cutoff - relativedelta(months=1))
    
    return start_date, end_date


def calculate_budget_progress(spent: float, limit: float) -> float:
    """Calcular porcentaje de uso de presupuesto"""
    if limit == 0:
        return 0.0
    return (spent / limit) * 100.0


def calculate_goal_progress(current: float, target: float) -> float:
    """Calcular progreso de meta"""
    if target == 0:
        return 0.0
    return (current / target) * 100.0


def project_goal_completion(current: float, target: float, monthly_contribution: float) -> int:
    """
    Proyectar meses para completar meta
    Returns: número de meses
    """
    if monthly_contribution <= 0:
        return -1  # No se puede calcular
    
    remaining = target - current
    if remaining <= 0:
        return 0  # Ya completada
    
    months = remaining / monthly_contribution
    return int(months) + (1 if months % 1 > 0 else 0)


def calculate_investment_return(purchase_price: float, current_price: float, quantity: float) -> Tuple[float, float]:
    """
    Calcular retorno de inversión
    Returns: (ganancia absoluta, ganancia porcentual)
    """
    cost_basis = purchase_price * quantity
    market_value = current_price * quantity
    absolute_gain = market_value - cost_basis
    
    if cost_basis == 0:
        percentage_gain = 0.0
    else:
        percentage_gain = (absolute_gain / cost_basis) * 100.0
    
    return absolute_gain, percentage_gain


def estimate_budget_depletion_date(spent: float, limit: float, days_elapsed: int, 
                                   total_days_in_period: int) -> date:
    """
    Estimar fecha en que se agotará el presupuesto
    """
    if days_elapsed == 0:
        return None
    
    daily_average = spent / days_elapsed
    remaining = limit - spent
    
    if daily_average <= 0:
        return None
    
    days_until_depletion = remaining / daily_average
    
    if days_until_depletion < 0:
        return date.today()  # Ya se agotó
    
    return date.today() + timedelta(days=int(days_until_depletion))

