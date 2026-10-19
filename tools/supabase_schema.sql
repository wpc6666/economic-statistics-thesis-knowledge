-- =====================================================================
-- Supabase 建表脚本 v2 - 经济统计学答题系统（含错题本高级功能）
-- 用法：Supabase Dashboard → SQL Editor → New query → 粘贴执行
-- 如果之前已执行过 v1，直接跑下面的 ALTER 部分即可
-- =====================================================================

-- ---------- 1. 答题进度表 ----------
CREATE TABLE IF NOT EXISTS user_progress (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  q_id        text NOT NULL,
  done        boolean DEFAULT false,
  correct     boolean DEFAULT false,
  selected    text,
  created_at  timestamptz DEFAULT now(),
  updated_at  timestamptz DEFAULT now(),
  UNIQUE(user_id, q_id)
);

-- ---------- 2. 错题本主表 ----------
-- 每道做错过的选择题一条记录；连续对3次后 mastered=true
CREATE TABLE IF NOT EXISTS wrong_questions (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  q_id                text NOT NULL,
  consecutive_correct int DEFAULT 0,       -- 连续答对计数（对1次+1，错了清零）
  total_wrong         int DEFAULT 0,       -- 总共做错次数
  total_correct       int DEFAULT 0,       -- 总共做对次数
  mastered            boolean DEFAULT false, -- 连续对3次后 true
  last_wrong_at       timestamptz,         -- 最近一次做错时间
  last_wrong_selected text,                -- 最近一次选错的选项
  created_at          timestamptz DEFAULT now(),
  updated_at          timestamptz DEFAULT now(),
  UNIQUE(user_id, q_id)
);

-- ---------- 3. 错题历史表（每次做错都记一条） ----------
CREATE TABLE IF NOT EXISTS wrong_history (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  q_id       text NOT NULL,
  selected   text NOT NULL,           -- 当时选的错误答案
  wrong_at   timestamptz DEFAULT now()
);

-- ---------- 4. 更新时间触发器 ----------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_progress_updated ON user_progress;
CREATE TRIGGER trg_user_progress_updated
  BEFORE UPDATE ON user_progress
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_wrong_questions_updated ON wrong_questions;
CREATE TRIGGER trg_wrong_questions_updated
  BEFORE UPDATE ON wrong_questions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ---------- 5. 开启 RLS ----------
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE wrong_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE wrong_history ENABLE ROW LEVEL SECURITY;

-- ---------- 6. RLS 策略：每个用户只能读写自己的数据 ----------
-- user_progress
DROP POLICY IF EXISTS "user_progress_select_own" ON user_progress;
CREATE POLICY "user_progress_select_own" ON user_progress FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "user_progress_insert_own" ON user_progress;
CREATE POLICY "user_progress_insert_own" ON user_progress FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "user_progress_update_own" ON user_progress;
CREATE POLICY "user_progress_update_own" ON user_progress FOR UPDATE USING (auth.uid() = user_id);

-- wrong_questions
DROP POLICY IF EXISTS "wrong_questions_select_own" ON wrong_questions;
CREATE POLICY "wrong_questions_select_own" ON wrong_questions FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "wrong_questions_insert_own" ON wrong_questions;
CREATE POLICY "wrong_questions_insert_own" ON wrong_questions FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "wrong_questions_update_own" ON wrong_questions;
CREATE POLICY "wrong_questions_update_own" ON wrong_questions FOR UPDATE USING (auth.uid() = user_id);

-- wrong_history
DROP POLICY IF EXISTS "wrong_history_select_own" ON wrong_history;
CREATE POLICY "wrong_history_select_own" ON wrong_history FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "wrong_history_insert_own" ON wrong_history;
CREATE POLICY "wrong_history_insert_own" ON wrong_history FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ---------- 7. 索引 ----------
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_wrong_questions_user_id ON wrong_questions(user_id);
CREATE INDEX IF NOT EXISTS idx_wrong_questions_unmastered ON wrong_questions(user_id, mastered);
CREATE INDEX IF NOT EXISTS idx_wrong_history_user_q ON wrong_history(user_id, q_id);

-- =====================================================================
-- 从 v1 升级到 v2 的迁移（如果之前建过 v1 表，跑这几句）：
-- ALTER TABLE wrong_questions ADD COLUMN IF NOT EXISTS consecutive_correct int DEFAULT 0;
-- ALTER TABLE wrong_questions ADD COLUMN IF NOT EXISTS total_wrong int DEFAULT 0;
-- ALTER TABLE wrong_questions ADD COLUMN IF NOT EXISTS total_correct int DEFAULT 0;
-- ALTER TABLE wrong_questions ADD COLUMN IF NOT EXISTS mastered boolean DEFAULT false;
-- ALTER TABLE wrong_questions ADD COLUMN IF NOT EXISTS last_wrong_at timestamptz;
-- ALTER TABLE wrong_questions ADD COLUMN IF NOT EXISTS last_wrong_selected text;
-- 然后 CREATE TABLE IF NOT EXISTS wrong_history (...) 上面那句。
-- =====================================================================
