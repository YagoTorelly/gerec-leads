insert into public.system_settings(singleton) values (true) on conflict (singleton) do nothing;

insert into public.business_holidays(holiday_date, scope, name) values
  ('2026-01-01', 'national', 'Confraternização Universal'),
  ('2026-04-21', 'national', 'Tiradentes'),
  ('2026-09-07', 'national', 'Independência do Brasil'),
  ('2026-10-12', 'national', 'Nossa Senhora Aparecida'),
  ('2026-11-02', 'national', 'Finados'),
  ('2026-11-15', 'national', 'Proclamação da República'),
  ('2026-11-20', 'national', 'Consciência Negra'),
  ('2026-12-25', 'national', 'Natal')
on conflict do nothing;
