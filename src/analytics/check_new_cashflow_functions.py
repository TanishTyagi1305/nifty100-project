from src.analytics.cashflow_kpis import cfo_quality_score, capex_intensity, is_distress_signal, is_deleveraging

print(cfo_quality_score(150, 100))    # expect (1.5, 'High Quality')
print(cfo_quality_score(30, 100))     # expect (0.3, 'Accrual Risk')
print(capex_intensity(-150, 1000))    # expect (15.0, 'Capital Intensive')
print(is_distress_signal(-50, 100))   # expect True
print(is_distress_signal(50, 100))    # expect False
print(is_deleveraging(-50, 800, 1000))  # expect True (borrowings dropped 1000->800)