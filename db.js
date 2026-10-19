// =====================================================================
// db.js - 答题系统数据持久化层（localStorage + Supabase 双后端）
// v2：错题本高级功能（连续对3次过关、错误历史、随机练习）
// =====================================================================

const SUPABASE_URL = 'https://tllxdxvvkbemxfsmkefx.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_hl469uoPet8zxeQ4hpMLGw_k_g-XyyL';

const STORAGE_KEY = 'exam_progress_v1';
const MASTER_THRESHOLD = 3; // 连续对3次才算掌握

window.DB = (function () {
  'use strict';

  let sbClient = null;
  let sbReady = false;
  let currentUser = null;
  let listeners = [];

  // 内存进度对象
  // wrong_meta: { [qid]: { consecutive_correct, total_wrong, total_correct, mastered,
  //                       last_wrong_at, last_wrong_selected, history: [{at, selected}] } }
  let memoryProgress = { choice: {}, subjective: {}, mock: {}, wrong_questions: [], wrong_meta: {} };

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      const s = document.createElement('script');
      s.src = src;
      s.onload = resolve;
      s.onerror = function () { reject(new Error('脚本加载失败: ' + src)); };
      document.head.appendChild(s);
    });
  }

  function loadLocal() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        memoryProgress.choice = parsed.choice || {};
        memoryProgress.subjective = parsed.subjective || {};
        memoryProgress.mock = parsed.mock || {};
        memoryProgress.wrong_questions = parsed.wrong_questions || [];
        memoryProgress.wrong_meta = parsed.wrong_meta || {};
      }
    } catch (e) {
      memoryProgress = { choice: {}, subjective: {}, mock: {}, wrong_questions: [], wrong_meta: {} };
    }
  }

  function writeLocal() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(memoryProgress));
    } catch (e) {}
  }

  function notify() {
    listeners.forEach(function (fn) { try { fn(); } catch (e) {} });
  }

  // ---------- Supabase 初始化 ----------
  async function initSupabase() {
    if (sbClient) return sbClient;
    try {
      await loadScript('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2');
      sbClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
      sbReady = true;

      sbClient.auth.onAuthStateChange(function (event, session) {
        currentUser = session ? session.user : null;
        if (currentUser) {
          pullFromCloud().then(notify);
        } else {
          loadLocal();
          notify();
        }
      });

      const { data: { session } } = await sbClient.auth.getSession();
      currentUser = session ? session.user : null;
      if (currentUser) {
        await pullFromCloud();
        notify();
      }
    } catch (e) {
      console.warn('[DB] Supabase 初始化失败，降级 localStorage', e);
      sbClient = null;
    }
    return sbClient;
  }

  // ---------- 云端拉取 ----------
  async function pullFromCloud() {
    if (!sbClient || !currentUser) return;
    try {
      const { data: progRows } = await sbClient.from('user_progress')
        .select('q_id, done, correct, selected').eq('user_id', currentUser.id);
      const { data: wrongRows } = await sbClient.from('wrong_questions')
        .select('q_id, consecutive_correct, total_wrong, total_correct, mastered, last_wrong_at, last_wrong_selected')
        .eq('user_id', currentUser.id);

      const newChoice = {}, newSubj = {}, newMock = {}, newWrongMeta = {};
      (progRows || []).forEach(function (r) {
        if (r.q_id.indexOf('mock_') === 0) newMock[r.q_id.slice(5)] = { completed: r.done };
        else if (r.q_id.indexOf('_s') > 0 || r.q_id.indexOf('_l') > 0) newSubj[r.q_id] = true;
        else newChoice[r.q_id] = { done: r.done, correct: r.correct, selected: r.selected };
      });

      const wrongList = [];
      (wrongRows || []).forEach(function (r) {
        newWrongMeta[r.q_id] = {
          consecutive_correct: r.consecutive_correct || 0,
          total_wrong: r.total_wrong || 0,
          total_correct: r.total_correct || 0,
          mastered: r.mastered || false,
          last_wrong_at: r.last_wrong_at,
          last_wrong_selected: r.last_wrong_selected,
          history: []
        };
        if (!r.mastered) wrongList.push(r.q_id);
      });

      memoryProgress.choice = newChoice;
      memoryProgress.subjective = newSubj;
      memoryProgress.mock = newMock;
      memoryProgress.wrong_questions = wrongList;
      memoryProgress.wrong_meta = newWrongMeta;
      writeLocal();
    } catch (e) {
      console.warn('[DB] 拉取云端失败', e);
    }
  }

  // ---------- 云端 upsert 错题统计 ----------
  async function pushWrongMetaToCloud(qid, meta) {
    if (!sbClient || !currentUser) return;
    try {
      await sbClient.from('wrong_questions').upsert({
        user_id: currentUser.id,
        q_id: qid,
        consecutive_correct: meta.consecutive_correct,
        total_wrong: meta.total_wrong,
        total_correct: meta.total_correct,
        mastered: meta.mastered,
        last_wrong_at: meta.last_wrong_at,
        last_wrong_selected: meta.last_wrong_selected,
        updated_at: new Date().toISOString()
      }, { onConflict: 'user_id,q_id' });
    } catch (e) {}
  }

  // ---------- 云端 insert 错误历史 ----------
  async function pushWrongHistory(qid, selected) {
    if (!sbClient || !currentUser) return;
    try {
      await sbClient.from('wrong_history').insert({
        user_id: currentUser.id,
        q_id: qid,
        selected: selected,
        wrong_at: new Date().toISOString()
      });
    } catch (e) {}
  }

  loadLocal();
  initSupabase();

  // ==================== 对外接口 ====================
  return {
    isLoggedIn: function () { return !!currentUser; },
    getUser: function () { return currentUser; },
    onChange: function (fn) { listeners.push(fn); },

    loadProgress: function () { return memoryProgress; },

    saveProgress: function (p) {
      memoryProgress = p || memoryProgress;
      memoryProgress.choice = memoryProgress.choice || {};
      memoryProgress.subjective = memoryProgress.subjective || {};
      memoryProgress.mock = memoryProgress.mock || {};
      memoryProgress.wrong_questions = memoryProgress.wrong_questions || [];
      memoryProgress.wrong_meta = memoryProgress.wrong_meta || {};
      writeLocal();
    },

    /**
     * 记录选择题答题结果，自动更新错题统计
     * 判错：total_wrong++，consecutive_correct=0，记入错题本
     * 判对：total_correct++，consecutive_correct++，>=3 则 mastered 并移出错题本
     */
    recordChoice: function (qid, record) {
      memoryProgress.choice[qid] = record;

      // 初始化或获取错题元数据
      if (!memoryProgress.wrong_meta[qid]) {
        memoryProgress.wrong_meta[qid] = {
          consecutive_correct: 0, total_wrong: 0, total_correct: 0,
          mastered: false, last_wrong_at: null, last_wrong_selected: null, history: []
        };
      }
      const meta = memoryProgress.wrong_meta[qid];

      if (!record.correct) {
        // 答错
        meta.total_wrong++;
        meta.consecutive_correct = 0;
        meta.last_wrong_at = new Date().toISOString();
        meta.last_wrong_selected = record.selected;
        meta.history.push({ at: meta.last_wrong_at, selected: record.selected });
        // 加入错题本（如果没掌握）
        if (!meta.mastered && !memoryProgress.wrong_questions.includes(qid)) {
          memoryProgress.wrong_questions.push(qid);
        }
        pushWrongHistory(qid, record.selected);
      } else {
        // 答对
        meta.total_correct++;
        meta.consecutive_correct++;
        // 连续对够次数 → 掌握
        if (meta.consecutive_correct >= MASTER_THRESHOLD && !meta.mastered) {
          meta.mastered = true;
          memoryProgress.wrong_questions = memoryProgress.wrong_questions.filter(function (x) { return x !== qid; });
        }
      }
      pushWrongMetaToCloud(qid, meta);
      writeLocal();
    },

    recordSubjective: function (qid) {
      memoryProgress.subjective[qid] = true;
      writeLocal();
      if (sbClient && currentUser) {
        sbClient.from('user_progress').upsert({
          user_id: currentUser.id, q_id: qid, done: true, correct: false, selected: null,
          updated_at: new Date().toISOString()
        }, { onConflict: 'user_id,q_id' }).catch(function(){});
      }
    },

    getWrongList: function () { return memoryProgress.wrong_questions.slice(); },

    /** 获取错题元数据 */
    getWrongMeta: function (qid) { return memoryProgress.wrong_meta[qid]; },

    // ---------- Auth ----------
    signUp: async function (email, password) {
      await initSupabase();
      if (!sbClient) throw new Error('云端服务暂不可用');
      const { data, error } = await sbClient.auth.signUp({ email: email, password: password });
      if (error) throw error;
      return data;
    },
    signIn: async function (email, password) {
      await initSupabase();
      if (!sbClient) throw new Error('云端服务暂不可用');
      const { data, error } = await sbClient.auth.signInWithPassword({ email: email, password: password });
      if (error) throw error;
      currentUser = data.user;
      await pullFromCloud();
      notify();
      return data;
    },
    signOut: async function () {
      if (sbClient) { try { await sbClient.auth.signOut(); } catch (e) {} }
      currentUser = null;
      loadLocal();
      notify();
    },
    refresh: async function () { await pullFromCloud(); notify(); }
  };
})();
