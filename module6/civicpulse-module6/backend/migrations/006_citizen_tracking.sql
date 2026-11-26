-- Module 6: NEW tables only (does not touch Module 1 tables). Assumes UUID ids, PostgreSQL 13+.
CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
  kind TEXT NOT NULL, status TEXT, status_history_id UUID,
  is_read BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read, created_at DESC);

CREATE TABLE IF NOT EXISTS comment_translations (
  status_history_id UUID NOT NULL REFERENCES status_history(id) ON DELETE CASCADE,
  lang TEXT NOT NULL, text TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (status_history_id, lang));

-- Integration hook: every status_history insert (Module 5 or Module 2's initial
-- 'submitted' row) notifies every citizen who reported that complaint. Module 5 needs no code change.
CREATE OR REPLACE FUNCTION m6_notify_status() RETURNS trigger AS $$
BEGIN
  INSERT INTO notifications(user_id, complaint_id, kind, status, status_history_id)
  SELECT DISTINCT r.user_id, NEW.complaint_id, 'status_change',
         lower(replace(NEW.new_status, ' ', '_')), NEW.id
  FROM reports r WHERE r.complaint_id = NEW.complaint_id AND r.user_id IS NOT NULL;
  RETURN NEW;
END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_m6_notify_status ON status_history;
CREATE TRIGGER trg_m6_notify_status AFTER INSERT ON status_history
  FOR EACH ROW EXECUTE FUNCTION m6_notify_status();
