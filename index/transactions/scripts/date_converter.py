import datetime, calendar, pydantic
from typing import Optional, Dict, List

class ConvertedDate(pydantic.BaseModel):
    date_start: Optional[datetime.datetime] = None
    date_end: Optional[datetime.datetime] = None
    excluded_date_periods: List[str] = []

def parse_date_condition_value(date_str: str) -> Optional[datetime.datetime]:
    """Essaie de parser une date YYYY-MM-DD, YYYY-MM, ou YYYY en datetime."""
    try:
        if len(date_str) == 10:  # YYYY-MM-DD
            return datetime.datetime.strptime(date_str, "%Y-%m-%d")
        elif len(date_str) == 7:  # YYYY-MM
            # Deviendra le 1er du mois. `build` l'ajustera pour date_end.
            return datetime.datetime.strptime(date_str, "%Y-%m")
        elif len(date_str) == 4:  # YYYY
            # Deviendra le 1er Jan. `build` l'ajustera pour date_end.
            return datetime.datetime.strptime(date_str, "%Y")
    except ValueError:
        return None
    return None

def convert_date(parser_output: Dict) -> ConvertedDate:

    date_conditions = parser_output.get('date_conditions', [])
    result = ConvertedDate()

    # Phase 1: Déterminer la plage globale date_start / date_end
    for condition in date_conditions:
        cond_type = condition.get('type')
        temp_ds: Optional[datetime.datetime] = None
        temp_de: Optional[datetime.datetime] = None

        if cond_type == 'exact_date':
            dt_val = parse_date_condition_value(condition.get('date', ''))
            if dt_val:
                temp_ds = dt_val
                temp_de = dt_val.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif cond_type == 'year':
            year = condition.get('year')
            if year:
                temp_ds = datetime.datetime(int(year), 1, 1)
                temp_de = datetime.datetime(int(year), 12, 31, 23, 59, 59, 999999)
        elif cond_type == 'month_year':
            year = condition.get('year')
            month = condition.get('month')
            if year and month:
                year, month = int(year), int(month)
                temp_ds = datetime.datetime(year, month, 1)
                _, last_day = calendar.monthrange(year, month)
                temp_de = datetime.datetime(year, month, last_day, 23, 59, 59, 999999)
        elif cond_type == 'range':
            ds_str = condition.get('from')
            de_str = condition.get('to')
            if ds_str: temp_ds = parse_date_condition_value(ds_str)
            if de_str:
                _temp_de = parse_date_condition_value(de_str)
                if _temp_de:
                    if len(de_str) == 10:  # YYYY-MM-DD
                        temp_de = _temp_de.replace(hour=23, minute=59, second=59, microsecond=999999)
                    elif len(de_str) == 7:  # YYYY-MM
                        _, last_day = calendar.monthrange(_temp_de.year, _temp_de.month)
                        temp_de = datetime.datetime(_temp_de.year, _temp_de.month, last_day, 23, 59, 59, 999999)
                    elif len(de_str) == 4:  # YYYY
                        temp_de = datetime.datetime(_temp_de.year, 12, 31, 23, 59, 59, 999999)
        elif cond_type == 'year_range':
            year_from = condition.get('from')
            year_to = condition.get('to')
            if year_from: temp_ds = datetime.datetime(int(year_from), 1, 1)
            if year_to: temp_de = datetime.datetime(int(year_to), 12, 31, 23, 59, 59, 999999)
        elif cond_type == 'after':
            dt_val = parse_date_condition_value(condition.get('date', ''))
            if dt_val: temp_ds = dt_val
        elif cond_type == 'after_year':
            year = condition.get('year')
            if year: temp_ds = datetime.datetime(int(year), 1, 1)
        elif cond_type == 'before':  # non-inclusive end
            dt_val = parse_date_condition_value(condition.get('date', ''))
            if dt_val:
                # Parser donne "avant JJ/MM/AAAA" ce qui signifie que la date elle-même est exclue
                # Donc date_end est la veille à 23:59:59
                temp_de = dt_val - datetime.timedelta(microseconds=1)
        elif cond_type == 'before_year':  # non-inclusive end
            year = condition.get('year')
            if year:
                # Avant l'année YYYY signifie jusqu'au 31 décembre YYYY-1
                temp_de = datetime.datetime(int(year) - 1, 12, 31, 23, 59, 59, 999999)

        if temp_ds:
            current_date_start = max(current_date_start, temp_ds) if current_date_start else temp_ds
        if temp_de:
            current_date_end = min(current_date_end, temp_de) if current_date_end else temp_de

    result.date_start = current_date_start
    result.date_end = current_date_end

    # Phase 2: Gérer les exclusions de date, potentiellement basées sur la plage globale
    excluded_periods_list = []
    for condition in date_conditions:
        cond_type = condition.get('type')
        if cond_type == 'exclude_month':
            month_to_exclude = condition.get('month')
            year_for_excluded_month = condition.get('year')  # Si le parser fournit l'année

            if month_to_exclude:
                month_to_exclude = int(month_to_exclude)
                if year_for_excluded_month:  # Cas "pas en juin 2012"
                    excluded_periods_list.append(f"{int(year_for_excluded_month):04d}-{month_to_exclude:02d}")
                elif current_date_start and current_date_end:  # Cas "entre X et Y mais pas en juin"
                    start_y = current_date_start.year
                    end_y = current_date_end.year
                    for year_iter in range(start_y, end_y + 1):
                        # Vérifier si le mois est DANS la plage effective de current_date_start/end
                        excl_period_month_start = datetime.datetime(year_iter, month_to_exclude, 1)
                        _, last_day_excl_month = calendar.monthrange(year_iter, month_to_exclude)
                        excl_period_month_end = datetime.datetime(year_iter, month_to_exclude, last_day_excl_month,
                                                                    23, 59, 59, 999999)

                        # Check if [excl_start, excl_end] overlaps with [current_date_start, current_date_end]
                        # Overlap exists if excl_start <= current_end AND excl_end >= current_start
                        if excl_period_month_start <= current_date_end and excl_period_month_end >= current_date_start:
                            excluded_periods_list.append(f"{year_iter:04d}-{month_to_exclude:02d}")
                # else: On ne peut pas déterminer l'année pour l'exclusion du mois.
        elif cond_type == 'exclude_period':  # Exemple: "sauf la semaine du X au Y"
            from_date_str = condition.get('from')
            to_date_str = condition.get('to')
            if from_date_str and to_date_str:
                # Assume format YYYY-MM-DD/YYYY-MM-DD from parser
                excluded_periods_list.append(f"{from_date_str}/{to_date_str}")
            elif from_date_str:  # Si juste une date ou un mois ou une année à exclure.
                excluded_periods_list.append(from_date_str)

    result.excluded_date_periods = list(set(excluded_periods_list))

    # S'assurer que les dates ont un fuseau horaire si possible (par défaut UTC si naïves)
    # Ceci est une convention, cela dépend de comment les dates des documents sont stockées.
    # Si les dates des documents sont naïves et supposées locales, il faudrait ajuster.
    # Pour l'instant, on va les rendre aware à UTC si elles sont naïves.
    # Cela devrait idéalement être géré de manière plus globale (ex: configurer un TZ par défaut).
    default_tz = datetime.timezone.utc  # Ou un autre fuseau pertinent

    if result.date_start and result.date_start.tzinfo is None:
        result.date_start = result.date_start.replace(tzinfo=default_tz)

    if result.date_end and result.date_end.tzinfo is None:
        result.date_end = result.date_end.replace(tzinfo=default_tz)