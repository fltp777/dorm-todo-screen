-- Stage 2C fixed-v2 state extension.  Review and run manually in Supabase.
-- This migration does not change RLS policies or create a second state table.

alter table public.screen_state
  add column if not exists daily_reminder_text text not null default '',
  add column if not exists yijing_position integer not null default 0;

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'screen_state_daily_reminder_length_check'
  ) then
    alter table public.screen_state add constraint screen_state_daily_reminder_length_check
      check (char_length(daily_reminder_text) <= 300);
  end if;
  if not exists (
    select 1 from pg_constraint where conname = 'screen_state_yijing_position_check'
  ) then
    alter table public.screen_state add constraint screen_state_yijing_position_check
      check (yijing_position >= 0 and yijing_position < 450);
  end if;
end $$;

-- Keep the existing authenticated-only data model.  New fields need explicit
-- column grants because the Stage 1C schema granted UPDATE(text) only.
grant update (text, daily_reminder_text, yijing_position) on table public.screen_state to authenticated;
