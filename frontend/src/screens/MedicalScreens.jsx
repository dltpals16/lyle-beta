import { useState, useEffect, useRef } from 'react';
import { theme, inputStyle, btnPrimary } from '../styles/theme';
import { Fade, Header } from '../components/Layout';
import {
  TREATMENT_STAGES, IVF_PHASE_OPTIONS, FET_CYCLE_OPTIONS,
  EMOTIONS, EMOTION_HISTORY, REGIONS, INFERTILITY_DURATIONS, DIAGNOSIS_OPTIONS, PROTOCOL_OPTIONS, getCycleOptionsForStage,
} from '../data/constants';
import {
  getTimelineWithStatus, getCurrentStageInfo, getTodayTasks,
} from '../data/timeline';
import { saveUserProfile } from '../auth/firebase';

// ==================== HOME ====================
const PRIVACY_POLICY_TEXT = `개인정보처리방침

라일(Lyle) (이하 '서비스')은 「개인정보 보호법」 제30조에 따라 이용자의 개인정보를 보호하고 이와 관련한 고충을 신속하고 원활하게 처리할 수 있도록 하기 위하여 다음과 같이 개인정보처리방침을 수립·공개합니다.

시행일자: 2025년 3월 20일

제1조 (개인정보의 수집 항목 및 수집 방법)

1. 수집하는 개인정보 항목

가. 일반 개인정보
• 닉네임
• 생년월일
• 거주지(시/도 단위)
• 기혼 여부
• 휴대전화번호 (알림 서비스 신청 시)

나. 민감정보 (별도 동의 필수)
• 건강 및 의료 관련 정보 (난임 진단명, 시술 단계 및 회차, 생리 시작일, 생리 주기, 복용 중인 약물·영양제, 기타 이용자가 대화 중 직접 제공한 건강 관련 정보 등)

※ 게스트 모드로 이용 시에는 어떠한 개인정보도 수집하지 않습니다.

다. 자동 수집 정보
서비스 이용 과정에서 IP 주소, 쿠키(Cookie), 접속 로그, 기기 정보(OS, 모델명, 브라우저 종류) 등이 자동으로 생성·수집될 수 있습니다.

2. 수집 방법
• 이용자가 서비스 내에서 직접 입력하는 방식
• 서비스 내 AI 상담 대화 과정에서 이용자가 자발적으로 제공한 건강 및 의료 관련 정보를 추출·저장하는 방식
• 서비스 이용 과정에서 자동으로 생성·수집되는 방식 (접속 로그, 기기 정보 등)

제2조 (개인정보의 수집 및 이용 목적)

수집한 개인정보는 다음의 목적을 위해 이용됩니다.
• 서비스 제공: 이용자 맞춤형 난임 치료 정보 및 콘텐츠 제공
• 알림 서비스: 카카오톡 알림톡을 통한 치료 일정 안내 및 정보성 메시지 발송
• 서비스 개선: 이용 통계 분석 및 서비스 품질 향상

제3조 (민감정보의 처리)

서비스는 이용자의 건강 및 의료 관련 정보를 「개인정보 보호법」 제23조에 따라 민감정보로 분류하여 처리합니다.
• 민감정보는 일반 개인정보와 별도로 명시적 동의를 받아 수집합니다.
• 수집된 민감정보는 오직 이용자 맞춤형 서비스 제공 목적으로만 이용됩니다.
• 대화 중 추출·저장된 건강 및 의료 관련 정보는 '기록됨' 카드를 통해 이용자에게 저장 사실을 즉시 고지합니다.
• 이용자는 '채팅 기억' 메뉴에서 저장된 정보를 직접 열람하고 삭제할 수 있습니다.
• 이용자의 대화 내용 및 건강·의료 관련 정보는 외부 AI 모델 학습에 사용되지 않습니다.

제4조 (개인정보의 보유 및 이용 기간)

• 회원 정보: 회원 탈퇴 시 즉시 파기
• 알림 서비스 관련 정보 (휴대전화번호): 알림 서비스 해지 시 즉시 파기
• 파기 방법: 전자적 파일 형태의 개인정보는 복구할 수 없는 기술적 방법을 사용하여 영구 삭제합니다.

제5조 (개인정보의 제3자 제공)

서비스는 이용자의 개인정보를 제3자에게 제공하지 않습니다. 다만, 이용자가 사전에 동의한 경우 또는 법령의 규정에 의한 경우는 예외로 합니다.

제6조 (개인정보 처리의 위탁)

• Google LLC (Firebase): 데이터 저장 및 호스팅
• OpenAI, L.L.C.: AI 상담 대화 처리 (텍스트 생성 및 응답)
  ※ OpenAI API를 통해 전송된 대화 내용은 AI 모델 학습에 사용되지 않습니다.
• 알리고: 카카오톡 알림톡 발송

제7조 (개인정보의 안전성 확보 조치)

• 데이터 전송 시 TLS(SSL) 암호화 적용
• 데이터 저장 시 AES-256 암호화 적용 (Google Cloud/Firebase 기본 제공)
• 개인정보 접근 권한의 최소화 및 관리

제8조 (이용자의 권리 및 행사 방법)

이용자는 언제든지 개인정보 열람, 정정·삭제, 처리 정지, 회원 탈퇴 및 동의 철회를 요청할 수 있습니다. 대화 중 수집·저장된 건강 및 의료 관련 정보는 '채팅 기억' 메뉴에서 직접 열람하고 삭제할 수 있습니다.

제9조 (개인정보 보호책임자)

• 성명: 이세민
• 이메일: arfoa.ai@gmail.com

제10조 (개인정보처리방침의 변경)

이 개인정보처리방침은 법령, 정책 또는 서비스 변경에 따라 수정될 수 있으며, 변경 시 서비스 내 공지사항 또는 알림톡을 통해 안내드립니다.

본 개인정보처리방침은 2025년 3월 20일부터 시행됩니다.`;

// ── 슬라이드 패널 (subpage) ──
function SlidePanel({ open, onClose, title, headerRight, children }) {
  return (
    <>
      {open && <div onClick={onClose} style={{
        position: 'fixed', inset: 0, background: 'rgba(28,24,38,0.3)', zIndex: 50,
      }} />}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, width: '100%', maxWidth: 480,
        background: theme.bg, zIndex: 51,
        transform: open ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.28s cubic-bezier(0.4,0,0.2,1)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        boxShadow: open ? '-4px 0 24px rgba(123,107,196,0.12)' : 'none',
      }}>
        <div style={{
          height: 52, display: 'flex', alignItems: 'center', gap: 4,
          padding: '0 8px 0 4px', borderBottom: `1px solid ${theme.border}`, flexShrink: 0,
        }}>
          <button onClick={onClose} style={{
            width: 44, height: 44, display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', borderRadius: '50%', border: 'none', background: 'none',
            fontSize: 18, color: theme.textSub,
          }}>←</button>
          <span style={{ fontSize: 16, fontWeight: 600, color: theme.text, flex: 1 }}>{title}</span>
          {headerRight}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px 24px' }}>
          {children}
        </div>
      </div>
    </>
  );
}

// ── 병원 일정 카드 (홈화면용) ──
function HomeAppointmentCard({ user, uid, stageInfo, onCheckQuestion, doctorQuestions, onQuestionAction }) {
  const [editingAppt, setEditingAppt] = useState(false);
  const [apptForm, setApptForm] = useState({
    hospital: user.hospital || '',
    date: user.nextAppointment || '',
    time: user.nextAppointmentTime || '',
  });
  const [showChecklist, setShowChecklist] = useState(false);

  const hospital = user.hospital;
  const apptDate = user.nextAppointment;
  const apptTime = user.nextAppointmentTime;
  const now = new Date();
  const apptType = stageInfo.nextStep ? stageInfo.nextStep.label : stageInfo.currentStep ? stageInfo.currentStep.label : '진료';

  let dDay = null;
  let isPast = false;
  if (apptDate) {
    const appt = new Date(apptDate + (apptTime ? 'T' + apptTime : 'T23:59'));
    const diff = Math.ceil((appt - now) / (1000 * 60 * 60 * 24));
    dDay = diff;
    isPast = appt < now;
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr + 'T00:00');
    const days = ['일', '월', '화', '수', '목', '금', '토'];
    return `${d.getMonth()+1}월 ${d.getDate()}일 (${days[d.getDay()]})`;
  };
  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const [h, m] = timeStr.split(':');
    const hour = parseInt(h);
    return `${hour < 12 ? '오전' : '오후'} ${hour > 12 ? hour - 12 : hour}:${m}`;
  };

  const saveAppt = async () => {
    try {
      await saveUserProfile(uid, {
        hospital: apptForm.hospital,
        nextAppointment: apptForm.date,
        nextAppointmentTime: apptForm.time,
      });
      setEditingAppt(false);
    } catch {}
  };

  const cardStyle = {
    padding: '20px 24px', borderRadius: theme.radius,
    border: `1px solid ${theme.border}`, background: theme.card,
    marginBottom: 16,
  };

  // 예약 지남 → 진료 결과 물어보기
  if (isPast) {
    return (
      <div style={cardStyle}>
        <div style={{ fontSize: 15, fontWeight: 700, color: theme.text, marginBottom: 8 }}>
          진료 결과는 어땠나요? 💜
        </div>
        <div style={{ fontSize: 13, color: theme.textSub, lineHeight: 1.6, marginBottom: 14 }}>
          선생님 말씀이나 검사 결과를 알려주시면, 앞으로의 케어에 반영할게요.
        </div>
        <button onClick={() => onCheckQuestion('진료 보고 왔어요')} style={{
          width: '100%', padding: '13px 0', borderRadius: 12,
          background: theme.primaryLight, border: 'none',
          color: theme.primary, fontSize: 14, fontWeight: 600, cursor: 'pointer',
        }}>라일에게 말해주러 가기 →</button>
      </div>
    );
  }

  // 정보 없음 or 편집 중 → 인라인 입력
  if ((!hospital && !apptDate) || editingAppt) {
    return (
      <div style={cardStyle}>
        <div style={{ fontSize: 15, fontWeight: 700, color: theme.text, marginBottom: 14 }}>
          다음 병원 일정 🩺
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <input value={apptForm.hospital} onChange={e => setApptForm(f => ({ ...f, hospital: e.target.value }))}
            placeholder="병원명 (예: 서울대병원 산부인과)"
            style={{ ...inputStyle, fontSize: 13, padding: '10px 14px' }} />
          <div style={{ display: 'flex', gap: 8 }}>
            <input type="date" value={apptForm.date} onChange={e => setApptForm(f => ({ ...f, date: e.target.value }))}
              style={{ ...inputStyle, fontSize: 13, padding: '10px 14px', flex: 1 }} />
            <input type="time" value={apptForm.time} onChange={e => setApptForm(f => ({ ...f, time: e.target.value }))}
              style={{ ...inputStyle, fontSize: 13, padding: '10px 14px', width: 120 }} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button onClick={saveAppt} style={{
            flex: 1, padding: '10px 0', borderRadius: 10,
            background: theme.primary, border: 'none',
            color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>저장</button>
          {editingAppt && (
            <button onClick={() => setEditingAppt(false)} style={{
              padding: '10px 16px', borderRadius: 10,
              background: 'none', border: `1px solid ${theme.border}`,
              color: theme.textSub, fontSize: 13, cursor: 'pointer',
            }}>취소</button>
          )}
        </div>
      </div>
    );
  }

  // 예약 있음 → 표시
  const uncheckedQuestions = doctorQuestions.filter(q => q.status !== 'checked');
  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: theme.text }}>다음 병원 일정</div>
        <button onClick={() => setEditingAppt(true)} style={{
          background: 'none', border: 'none', fontSize: 12, color: theme.primary, cursor: 'pointer', fontWeight: 500,
        }}>수정</button>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 10 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 12,
          background: theme.primaryLight, display: 'flex',
          alignItems: 'center', justifyContent: 'center', fontSize: 20, flexShrink: 0,
        }}>🩺</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: theme.primary, marginBottom: 2 }}>{apptType}</div>
          <div style={{ fontSize: 14, fontWeight: 500, color: theme.text }}>{hospital}</div>
          <div style={{ fontSize: 12, color: theme.textSub }}>
            {apptDate ? formatDate(apptDate) : ''}{apptTime ? ` ${formatTime(apptTime)}` : ''}
          </div>
        </div>
        {dDay !== null && (
          <div style={{ fontSize: 22, fontWeight: 700, color: theme.primary, flexShrink: 0 }}>
            {dDay === 0 ? 'D-Day' : dDay > 0 ? `D-${dDay}` : ''}
          </div>
        )}
      </div>

      {/* 진료 체크리스트 */}
      {uncheckedQuestions.length > 0 && (
        <div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${theme.border}` }}>
          <button onClick={() => setShowChecklist(!showChecklist)} style={{
            background: 'none', border: 'none', cursor: 'pointer', width: '100%',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: 0, color: theme.primary, fontSize: 13, fontWeight: 600,
          }}>
            <span>📋 진료 체크리스트 {uncheckedQuestions.length}개</span>
            <span style={{ fontSize: 11 }}>{showChecklist ? '▲' : '▼'}</span>
          </button>
          {showChecklist && (
            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {uncheckedQuestions.map(q => (
                <div key={q.id} style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 0', borderBottom: `1px solid ${theme.border}`,
                }}>
                  <button onClick={() => onQuestionAction(q.id, 'check')} style={{
                    width: 20, height: 20, borderRadius: 10, flexShrink: 0,
                    border: `2px solid ${theme.border}`, background: 'transparent',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 10,
                  }} />
                  <span style={{ fontSize: 13, color: theme.text }}>{q.content}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function HomeScreen({ setTab, user, uid, onCheckQuestion, onStartOnboarding, setUser }) {

  const [show, setShow] = useState(false);
  const [doctorQuestions, setDoctorQuestions] = useState([]);
  const [newQuestion, setNewQuestion] = useState('');
  const [addingQuestion, setAddingQuestion] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [guestModal, setGuestModal] = useState(false);
  const [showChecklist, setShowChecklist] = useState(true);
  const [showClinicMemo, setShowClinicMemo] = useState(false);
  const [clinicMemo, setClinicMemo] = useState('');
  const [pastVisits, setPastVisits] = useState([]);
  const [showTimeline, setShowTimeline] = useState(false);
  const [timelineEditing, setTimelineEditing] = useState(false);
  const [selectedTimelineStage, setSelectedTimelineStage] = useState(null);
  const [showPastVisits, setShowPastVisits] = useState(false);
  useEffect(() => { setShow(true); }, []);
  const isGuest = uid?.startsWith('guest_');
  const stageName = TREATMENT_STAGES.find(s => s.id === user.stage)?.label || '시술';
  const cycleText = (!user.cycle && user.cycle !== 0) ? '' : user.cycle === 0 ? '준비 중' : `${user.cycle}회차`;
  const stageInfo = getCurrentStageInfo(user.stage, user.periodDate, user.cycle, user.protocol, user.currentPhase, user.ivfPhase);

  const loadDoctorQuestions = () => {
    if (!uid) return;
    fetch(`/doctor-questions/${uid}`)
      .then(r => r.json())
      .then(data => setDoctorQuestions(data.questions || []))
      .catch(() => {});
  };
  useEffect(() => { loadDoctorQuestions(); }, [uid]);

  const toggleQuestion = async (qId, currentChecked) => {
    const action = currentChecked ? 'uncheck' : 'check';
    try {
      await fetch(`/doctor-questions/${uid}/${qId}/${action}`, { method: 'POST' });
      setDoctorQuestions(prev => prev.map(q =>
        q.id === qId ? { ...q, checked: !currentChecked } : q
      ));
    } catch (e) { console.error(e); }
  };

  const deleteQuestion = async (qId) => {
    try {
      await fetch(`/doctor-questions/${uid}/${qId}`, { method: 'DELETE' });
      setDoctorQuestions(prev => prev.filter(q => q.id !== qId));
    } catch (e) { console.error(e); }
  };

  const addQuestion = async () => {
    const text = newQuestion.trim();
    if (!text) return;
    try {
      const res = await fetch(`/doctor-questions/${uid}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
      });
      const data = await res.json();
      if (data.question) {
        setDoctorQuestions(prev => [...prev, data.question]);
      }
      setNewQuestion('');
      setAddingQuestion(false);
    } catch (e) { console.error(e); }
  };

  return (
    <div className="page-content" style={{ flex: 1, overflow: 'auto', padding: '0 24px 40px' }}>
      <div style={{ maxWidth: 960, margin: '0 auto', width: '100%' }}>
      {(() => {
        const apptDate = user.nextAppointment;
        const apptTime = user.nextAppointmentTime;
        let isPast = false;
        if (apptDate) {
          const appt = new Date(apptDate + (apptTime ? 'T' + apptTime : 'T23:59'));
          isPast = appt < new Date();
        }
        const greeting = isPast
          ? `진료 결과는 어땠나요? 라일에게 알려주세요! 💜`
          : `${user.name}님, 안녕하세요 👋`;
        return <Header
          title={<span>{greeting}</span>}
          subtitle={isGuest ? '' : `${stageName} · ${cycleText}`}
        />;
      })()}
      <div style={{ width: '100%' }}>
        <Fade show={show}>
          {isGuest ? (
          <div style={{
            background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 100%)`,
            borderRadius: 18, padding: '28px 24px', marginTop: 20, marginBottom: 20,
            color: '#fff', textAlign: 'center',
          }}>
            <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>계정을 등록하면 나만의 타임라인을 볼 수 있어요</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 16 }}>시술 단계별 일정 관리, 맞춤 알림, 진료 체크리스트까지</div>
            <button onClick={onStartOnboarding} style={{
              padding: '10px 24px', borderRadius: 12, border: '1.5px solid rgba(255,255,255,0.5)',
              background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}>계정 등록하기</button>
          </div>
          ) : (
          <div style={{
            background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 100%)`,
            borderRadius: 18, padding: '22px 24px 20px', marginTop: 20, marginBottom: 20,
            color: '#fff', position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ position: 'absolute', width: 160, height: 160, borderRadius: '50%', background: 'rgba(255,255,255,0.08)', top: -60, right: -40, pointerEvents: 'none' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{
                fontSize: 11, fontWeight: 600, background: 'rgba(255,255,255,0.2)',
                borderRadius: 20, padding: '3px 10px',
              }}>{stageName} {cycleText !== '준비 중' ? cycleText : ''} 진행 중</div>
              <button onClick={() => setShowTimeline(true)} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.85)',
              }}>전체 보기 →</button>
            </div>
            <div style={{ fontSize: 21, fontWeight: 700, letterSpacing: -0.5, marginBottom: 4 }}>
              {user.currentPhase === '휴식 중' ? '☕ 휴식 중' : stageInfo.currentStep ? stageInfo.currentStep.label : stageInfo.dayText}
            </div>
            <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 4 }}>
              {user.currentPhase === '휴식 중' ? '몸과 마음이 편안한 하루 보내세요 💜' : stageInfo.desc || ''}
            </div>
            {user.currentPhase === '휴식 중' && (
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button onClick={() => { window.__openProfileEdit = true; setTab('mypage'); }} style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                  🔄 새 주기 시작하기
                </button>
              </div>
            )}

            {/* 판정일 이후 또는 휴식 중 선택지 */}
            {(stageInfo.pastJudgment || user.currentPhase === '휴식 중') && user.currentPhase !== '휴식 중' && (
              <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                <button onClick={() => { window.__openProfileEdit = true; setTab('mypage'); }} style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                  🔄 새 주기 시작
                </button>
                <button onClick={() => setShowTimeline(true)} style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                  📋 단계 직접 지정
                </button>
                <button onClick={async () => {
                  await saveUserProfile(uid, { current_phase: '휴식 중', phase_changed_at: new Date().toISOString().split('T')[0] });
                  setUser(prev => ({ ...prev, currentPhase: '휴식 중' }));
                }} style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                  ☕ 휴식 중이에요
                </button>
              </div>
            )}

            {/* 프로그레스 바 — 타임라인 전체 단계 기준 */}
            {stageInfo.timeline && stageInfo.timeline.length > 0 && (
              <div style={{ margin: '14px 0 8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ fontSize: 10, opacity: 0.6 }}>{stageInfo.timeline[0]?.label}</span>
                  <span style={{ fontSize: 10, opacity: 0.6 }}>{stageInfo.timeline[stageInfo.timeline.length - 1]?.label}</span>
                </div>
                <div style={{ height: 4, background: 'rgba(255,255,255,0.18)', borderRadius: 2, position: 'relative' }}>
                  {(() => {
                    const currentIdx = stageInfo.timeline.findIndex(t => t.status === 'current');
                    const pct = currentIdx >= 0 ? Math.round((currentIdx / (stageInfo.timeline.length - 1)) * 100) : 0;
                    return <div style={{ height: '100%', width: `${pct}%`, background: 'rgba(255,255,255,0.85)', borderRadius: 2 }} />;
                  })()}
                  <div style={{
                    position: 'absolute', top: '50%', transform: 'translateY(-50%)',
                    left: 0, right: 0, display: 'flex', justifyContent: 'space-between', padding: '0 1px',
                  }}>
                    {stageInfo.timeline.map((t, idx) => {
                      const isCurrent = t.status === 'current';
                      const isPast = t.status === 'done';
                      return (
                        <div key={idx} style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                          <div style={{
                            width: isCurrent ? 10 : 7, height: isCurrent ? 10 : 7, borderRadius: '50%',
                            background: isPast ? 'rgba(255,255,255,0.9)' : isCurrent ? '#fff' : 'rgba(255,255,255,0.15)',
                            border: !isPast && !isCurrent ? '1.5px solid rgba(255,255,255,0.4)' : 'none',
                            boxShadow: isCurrent ? '0 0 0 2.5px rgba(255,255,255,0.4)' : 'none',
                          }} />
                          {isCurrent && (
                            <span style={{ position: 'absolute', top: 14, fontSize: 9, fontWeight: 600, color: '#fff', whiteSpace: 'nowrap' }}>
                              📍 {t.label}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* 임신 판정 단계이면 선택지 표시 */}
            {stageInfo.currentStep?.label === '임신 판정' && user.currentPhase !== '휴식 중' && (
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button onClick={() => { window.__openProfileEdit = true; setTab('mypage'); }} style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                  🔄 새 주기 시작
                </button>
                <button onClick={async () => { await saveUserProfile(uid, { current_phase: '휴식 중' }); setUser(prev => ({ ...prev, currentPhase: '휴식 중' })); }} style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
                  ☕ 휴식 중이에요
                </button>
              </div>
            )}

            {/* 하단 버튼 제거 — 상단 "전체 보기 →"로 이동 */}
          </div>
          )}
        </Fade>


        {/* 다음 병원 일정 + 진료 체크리스트 */}
        <Fade show={show} delay={80}>
          <div style={{
            borderRadius: theme.radius,
            border: `1px solid ${theme.border}`, background: theme.card,
            marginBottom: 16, overflow: 'hidden',
          }}>
            {/* 병원 일정 헤더 */}
            <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${theme.border}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: theme.text }}>다음 병원 일정</div>
                <span style={{ fontSize: 11, color: theme.textSub, background: theme.primaryBg, padding: '3px 10px', borderRadius: 10 }}>준비중</span>
              </div>
              {pastVisits.length > 0 && (
                <button onClick={() => setShowPastVisits(true)} style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 12, color: theme.primary, fontWeight: 500,
                }}>지난 진료 →</button>
              )}
            </div>

            {/* 진료 체크리스트 접이식 */}
            <div style={{ borderBottom: `1px solid ${theme.border}` }}>
              <button onClick={() => setShowChecklist(!showChecklist)} style={{
                width: '100%', padding: '12px 20px', background: 'none', border: 'none',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                cursor: 'pointer',
              }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: theme.primary }}>
                  📋 진료 체크리스트 {doctorQuestions.filter(q => !q.checked).length > 0 ? `${doctorQuestions.filter(q => !q.checked).length}개` : ''}
                </span>
                <span style={{ fontSize: 11, color: theme.textSub }}>{showChecklist ? '▲' : '▼'}</span>
              </button>

              {showChecklist && (
                <div style={{ padding: '0 20px 16px' }}>
                  {doctorQuestions.length === 0 ? (
                    <div style={{ fontSize: 13, color: theme.textSub, padding: '4px 0' }}>
                      아직 항목이 없어요. 대화하면서 자동으로 추가돼요.
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      {doctorQuestions.map(q => (
                        <div key={q.id} style={{
                          display: 'flex', alignItems: 'center', gap: 10,
                          padding: '10px 0', borderBottom: `1px solid ${theme.border}`,
                        }}>
                          <button onClick={() => toggleQuestion(q.id, q.checked)} style={{
                            width: 22, height: 22, borderRadius: 11, flexShrink: 0,
                            border: `2px solid ${q.checked ? theme.primary : theme.border}`,
                            background: q.checked ? theme.primary : 'transparent',
                            cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: '#fff', fontSize: 10,
                          }}>{q.checked ? '✓' : ''}</button>
                          <span style={{
                            flex: 1, fontSize: 13, color: theme.text,
                            textDecoration: q.checked ? 'line-through' : 'none',
                            opacity: q.checked ? 0.5 : 1,
                          }}>{q.content}</span>
                          <button onClick={async () => {
                            try { await fetch(`/doctor-questions/${uid}/${q.id}`, { method: 'DELETE' }); loadDoctorQuestions(); } catch {}
                          }} style={{
                            background: 'none', border: 'none', cursor: 'pointer',
                            color: theme.textSub, fontSize: 13, padding: '2px 4px', flexShrink: 0,
                          }}
                          onMouseEnter={e => e.target.style.color = '#e74c3c'}
                          onMouseLeave={e => e.target.style.color = theme.textSub}
                          >🗑️</button>
                        </div>
                      ))}
                    </div>
                  )}
                  {!addingQuestion ? (
                    <button onClick={() => { if (isGuest) { setGuestModal(true); return; } setAddingQuestion(true); }} style={{
                      marginTop: 10, fontSize: 13, color: theme.primary,
                      cursor: 'pointer', background: 'none', border: 'none', padding: 0,
                      display: 'flex', alignItems: 'center', gap: 4,
                    }}>
                      <span style={{ fontSize: 15 }}>+</span> 질문 추가
                    </button>
                  ) : (
                    <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                      <input value={newQuestion} onChange={e => setNewQuestion(e.target.value)}
                        placeholder="진료 시 물어볼 질문" onKeyDown={e => e.key === 'Enter' && addQuestion()}
                        style={{ ...inputStyle, fontSize: 13, flex: 1, padding: '8px 12px' }} autoFocus />
                      <button onClick={addQuestion} style={{
                        background: theme.primary, border: 'none', borderRadius: 8,
                        padding: '0 14px', color: '#fff', fontSize: 12, cursor: 'pointer',
                      }}>추가</button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 진료 메모 + 저장하기 (접이식) */}
            <div style={{ padding: '0 20px' }}>
              <button onClick={() => { if (isGuest) { setGuestModal(true); return; } setShowClinicMemo(v => !v); }} style={{
                background: 'none', border: 'none', cursor: 'pointer', padding: '14px 0', width: '100%',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                borderTop: `1px solid ${theme.border}`,
              }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: theme.primary }}>진료 메모</span>
                <span style={{ fontSize: 11, color: theme.textSub }}>{showClinicMemo ? '▲' : '▼'}</span>
              </button>
            </div>
            {showClinicMemo && (
            <div style={{ padding: '0 20px 14px' }}>
              <textarea
                value={clinicMemo}
                onChange={e => setClinicMemo(e.target.value)}
                placeholder="진료 후 선생님 말씀, 검사 결과 등을 자유롭게 적어보세요"
                style={{
                  ...inputStyle, fontSize: 13, padding: '10px 14px',
                  minHeight: 60, resize: 'vertical', lineHeight: 1.5,
                }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                <button onClick={async () => {
                  // 체크된 항목 + 메모를 지난 진료로 저장
                  const checkedItems = doctorQuestions.filter(q => q.checked).map(q => q.content);
                  const memo = clinicMemo.trim();
                  if (checkedItems.length === 0 && !memo) return;

                  const today = new Date().toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' });
                  const record = {
                    date: today,
                    questions: checkedItems,
                    memo: memo,
                  };

                  // 지난 진료 기록에 추가
                  setPastVisits(prev => [record, ...prev]);

                  // 채팅 기억에도 저장 (에이전트 연동)
                  const noteContent = [
                    `[진료 기록 ${today}]`,
                    ...checkedItems.map(q => `- ${q}`),
                    memo ? `메모: ${memo}` : '',
                  ].filter(Boolean).join('\n');

                  try {
                    await fetch(`/notes/${uid}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ content: noteContent }),
                    });
                  } catch {}

                  // 체크된 질문 삭제 + 메모 초기화
                  for (const q of doctorQuestions.filter(q => q.checked)) {
                    try { await fetch(`/doctor-questions/${uid}/${q.id}`, { method: 'DELETE' }); } catch {}
                  }
                  loadDoctorQuestions();
                  setClinicMemo('');
                  setShowChecklist(false);
                }} style={{
                  padding: '10px 24px', borderRadius: 10,
                  background: theme.primary, border: 'none',
                  color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
                }}>저장하기</button>
              </div>
            </div>
            )}

            {/* 지난 진료 링크 */}
            {pastVisits.length > 0 && (
              <div style={{ borderTop: `1px solid ${theme.border}`, padding: '12px 20px' }}>
                <button onClick={() => setShowPastVisits(true)} style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 13, color: theme.primary, fontWeight: 600, padding: 0,
                }}>지난 진료 {pastVisits.length}건 →</button>
              </div>
            )}
          </div>
        </Fade>

        {/* 다들 이런 거 물어봤어요 */}
        <Fade show={show} delay={160}>
          <div style={{
            borderRadius: theme.radius, border: `1px solid ${theme.border}`,
            background: theme.card, marginBottom: 16, padding: '20px 24px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: theme.text }}>
                다들 이런 거 물어봤어요
              </div>
              <span style={{ fontSize: 11, color: theme.textSub, background: theme.primaryBg, padding: '3px 10px', borderRadius: 10 }}>준비중</span>
            </div>
            <div style={{ fontSize: 13, color: theme.textSub }}>
              같은 단계의 사용자들이 자주 묻는 Q&A를 제공할 예정이에요.
            </div>
          </div>
        </Fade>

        {/* 오늘의 케어 */}
        <Fade show={show} delay={200}>
          <div style={{
            borderRadius: theme.radius, border: `1px solid ${theme.border}`,
            background: theme.card, marginBottom: 16, padding: '20px 24px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: theme.text }}>오늘의 케어</div>
              <span style={{ fontSize: 11, color: theme.textSub, background: theme.primaryBg, padding: '3px 10px', borderRadius: 10 }}>준비중</span>
            </div>
            <div style={{ fontSize: 13, color: theme.textSub }}>
              복용 중인 약, 주사 일정, 증상 기록을 관리할 수 있어요.
            </div>
          </div>
        </Fade>

        {/* 사업자 정보 */}
        <div style={{
          marginTop: 32, padding: '20px 0', borderTop: `1px solid ${theme.border}`,
          fontSize: 11, color: theme.textSub, lineHeight: 1.8,
        }}>
          <div style={{ marginBottom: 8 }}>
            <span onClick={() => setShowPrivacy(true)} style={{
              fontWeight: 700, fontSize: 12, color: theme.text, cursor: 'pointer',
              textDecoration: 'underline',
            }}>개인정보처리방침</span>
          </div>
          <div>(주)와이낫 | 대표 김다선</div>
          <div>사업자등록번호 501-29-19890</div>
          <div>통신판매업신고 제2021-서울서대문-1504호</div>
          <div>경기도 시흥시 거북섬1길 19, 2층 205호-A44호</div>
          <div>이메일 arfoa.ai@gmail.com</div>
          <div style={{ marginTop: 8, fontSize: 10, color: theme.textSub }}>Copyright © 와이낫. All rights reserved.</div>
        </div>
      </div>{/* maxWidth wrapper end */}

        {/* 게스트 기능 제한 모달 */}
        {guestModal && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.35)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={() => setGuestModal(false)}>
            <div onClick={e => e.stopPropagation()} style={{ background: '#fff', borderRadius: 16, padding: '28px 24px', maxWidth: 340, textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>계정 등록이 필요해요</div>
              <div style={{ fontSize: 13, color: '#8C82A6', marginBottom: 20, lineHeight: 1.6 }}>이 기능을 사용하려면 계정을 등록해주세요.</div>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                <button onClick={() => setGuestModal(false)} style={{ padding: '10px 20px', borderRadius: 10, border: `1px solid ${theme.border}`, background: '#fff', fontSize: 13, cursor: 'pointer' }}>닫기</button>
                <button onClick={onStartOnboarding} style={{ padding: '10px 20px', borderRadius: 10, border: 'none', background: theme.primary, color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>계정 등록하기</button>
              </div>
            </div>
          </div>
        )}

        {/* 개인정보처리방침 모달 */}
        {showPrivacy && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.5)', zIndex: 200,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }} onClick={() => setShowPrivacy(false)}>
            <div style={{
              background: '#fff', borderRadius: 16, padding: '24px 20px',
              width: '90%', maxWidth: 500, maxHeight: '80vh', overflow: 'auto',
            }} onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <span style={{ fontSize: 16, fontWeight: 700, color: theme.text }}>개인정보처리방침</span>
                <button onClick={() => setShowPrivacy(false)} style={{
                  background: 'none', border: 'none', fontSize: 20, color: theme.textSub, cursor: 'pointer',
                }}>×</button>
              </div>
              <div style={{ fontSize: 13, color: theme.text, lineHeight: 1.9, whiteSpace: 'pre-line' }}>
                {PRIVACY_POLICY_TEXT}
              </div>
            </div>
          </div>
        )}

        {/* 타임라인 슬라이드 패널 */}
        <SlidePanel open={showTimeline} onClose={() => { setShowTimeline(false); setTimelineEditing(false); }} title="타임라인"
          headerRight={
            <button onClick={async () => {
              if (timelineEditing) {
                if (selectedTimelineStage) {
                  try {
                    await saveUserProfile(uid, { current_phase: selectedTimelineStage, phase_changed_at: new Date().toISOString().split('T')[0] });
                    setUser(prev => ({ ...prev, currentPhase: selectedTimelineStage }));
                  } catch (e) { console.error(e); }
                }
                setSelectedTimelineStage(null);
                setTimelineEditing(false);
              } else {
                setSelectedTimelineStage(null);
                setTimelineEditing(true);
              }
            }} style={{
              background: 'none', border: 'none', fontSize: 13, fontWeight: 600,
              color: timelineEditing ? theme.accent : theme.primary, cursor: 'pointer', padding: '6px 12px',
            }}>{timelineEditing ? '완료' : '변경'}</button>
          }
        >
          {(() => {
            const timeline = getTimelineWithStatus(user.stage, user.periodDate, user.cycle, user.protocol, user.currentPhase, user.ivfPhase);
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                {timeline.map((item, i) => {
                  const isDone = item.status === 'done';
                  const isCurrent = item.status === 'current';
                  return (
                    <div key={i} style={{
                      display: 'flex', gap: 14,
                      cursor: timelineEditing ? 'pointer' : 'default',
                      borderRadius: 10,
                      background: selectedTimelineStage === item.label ? theme.primaryLight + '33' : 'transparent',
                    }}
                      onClick={() => {
                        if (!timelineEditing) return;
                        setSelectedTimelineStage(item.label);
                      }}
                    >
                      {/* 세로선 + 점 */}
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 20, flexShrink: 0 }}>
                        <div style={{
                          width: (timelineEditing ? selectedTimelineStage === item.label : isCurrent) ? 14 : 10,
                          height: (timelineEditing ? selectedTimelineStage === item.label : isCurrent) ? 14 : 10,
                          borderRadius: '50%',
                          background: timelineEditing
                            ? (selectedTimelineStage === item.label ? theme.primary : theme.border)
                            : (isDone ? theme.primary : isCurrent ? theme.primary : theme.border),
                          border: (timelineEditing ? selectedTimelineStage === item.label : isCurrent) ? `3px solid ${theme.primaryLight}` : 'none',
                          flexShrink: 0, marginTop: 4,
                        }} />
                        {i < timeline.length - 1 && (
                          <div style={{
                            width: 2, flex: 1, minHeight: 30,
                            background: isDone ? theme.primary : theme.border,
                          }} />
                        )}
                      </div>
                      {/* 내용 */}
                      <div style={{
                        paddingBottom: 20, flex: 1,
                        opacity: isDone && !timelineEditing ? 0.5 : 1,
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 18 }}>{item.icon}</span>
                          <span style={{
                            fontSize: 14, fontWeight: isCurrent ? 700 : 500,
                            color: isCurrent ? theme.primary : theme.text,
                          }}>{item.label}</span>
                          <span style={{ fontSize: 11, color: theme.textSub }}>Day {item.day}</span>
                          {(timelineEditing ? selectedTimelineStage === item.label : isCurrent) && <span style={{
                            fontSize: 10, fontWeight: 600, color: '#fff',
                            background: theme.primary, borderRadius: 10, padding: '2px 8px',
                          }}>{timelineEditing ? '선택' : '현재'}</span>}
                        </div>
                        <div style={{ fontSize: 12, color: theme.textSub, marginTop: 4, lineHeight: 1.6 }}>
                          {item.desc}
                        </div>
                        {false && (
                          <div style={{ fontSize: 11, color: theme.primary, marginTop: 4, fontWeight: 500 }}>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })()}
        </SlidePanel>

        {/* 지난 진료 슬라이드 패널 */}
        <SlidePanel open={showPastVisits} onClose={() => setShowPastVisits(false)} title="지난 진료">
          {pastVisits.length === 0 ? (
            <div style={{ fontSize: 14, color: theme.textSub, textAlign: 'center', padding: '40px 0' }}>
              아직 진료 기록이 없어요.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {pastVisits.map((visit, i) => (
                <div key={i} style={{
                  padding: '16px 18px', borderRadius: 12,
                  background: theme.card, border: `1px solid ${theme.border}`,
                }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: theme.textSub, marginBottom: 8 }}>{visit.date}</div>
                  {visit.questions.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      {visit.questions.map((q, qi) => (
                        <div key={qi} style={{
                          fontSize: 13, color: theme.textSub,
                          textDecoration: 'line-through', marginBottom: 3,
                        }}>{q}</div>
                      ))}
                    </div>
                  )}
                  {visit.memo && (
                    <div style={{
                      fontSize: 13, color: theme.primary,
                      background: theme.primaryLight, borderRadius: 8, padding: '8px 12px',
                      lineHeight: 1.5,
                    }}>📝 {visit.memo}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </SlidePanel>
      </div>
    </div>
  );
}

// ==================== TIMELINE ====================
export function TimelineScreen({ user, uid, setUser }) {
  const [show, setShow] = useState(false);
  const [phaseEditing, setPhaseEditing] = useState(false);
  const [phaseToast, setPhaseToast] = useState(null);
  useEffect(() => { setShow(true); }, []);
  const stageName = TREATMENT_STAGES.find(s => s.id === user.stage)?.label || '';
  const cycleText = user.cycle === 0 ? '준비 중' : `${user.cycle}회차`;
  const timeline = getTimelineWithStatus(user.stage, user.periodDate, user.cycle, user.protocol, user.currentPhase, user.ivfPhase);
  const stageInfo = getCurrentStageInfo(user.stage, user.periodDate, user.cycle, user.protocol, user.currentPhase, user.ivfPhase);

  const handlePhaseSelect = async (label) => {
    try {
      await saveUserProfile(uid, { current_phase: label, phase_changed_at: new Date().toISOString().split('T')[0] });
      setUser(prev => ({ ...prev, currentPhase: label }));
      setPhaseEditing(false);
      setPhaseToast('현재 단계가 업데이트됐어요!');
      setTimeout(() => setPhaseToast(null), 2000);
    } catch {
      setPhaseToast('저장에 실패했어요.');
      setTimeout(() => setPhaseToast(null), 2000);
    }
  };

  return (
    <div className="page-content" style={{ flex: 1, overflow: 'auto', padding: '0 24px 40px' }}>
      <Header title="타임라인" subtitle={`${stageName} · ${cycleText}`} />
      <div style={{ maxWidth: 960, margin: "0 auto" }}>
        <Fade show={show}>
          <div style={{
            padding: '14px 18px', borderRadius: 12, marginTop: 16, marginBottom: 16,
            background: phaseEditing ? theme.primaryLight : theme.primaryBg,
            border: `1px solid ${theme.primaryLight}`,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: theme.primary, fontWeight: 600 }}>
              <span>{(!user.cycle && !(user.stage === 'ivf' && user.ivfPhase && user.ivfPhase !== 'prep')) || user.stage === 'prep' ? '📋' : phaseEditing ? '👆' : '📍'}</span>
              {phaseEditing
                ? '지금 어느 단계에 계세요?'
                : (!user.cycle && !(user.stage === 'ivf' && user.ivfPhase && user.ivfPhase !== 'prep')) && user.stage !== 'prep'
                  ? `${stageName} 시술 예정 프로토콜`
                  : stageInfo.currentStep ? `현재 · ${stageInfo.currentStep.label}` : `${stageName} 진행 중`}
            </div>
            {(user.cycle > 0 || (user.stage === 'ivf' && user.ivfPhase && user.ivfPhase !== 'prep') || user.stage === 'fet') && user.stage !== 'prep' && (
              <button onClick={() => setPhaseEditing(p => !p)} style={{
                background: 'none', border: 'none', fontSize: 13, fontWeight: 600,
                color: phaseEditing ? '#C44' : theme.primary, cursor: 'pointer', padding: '2px 6px',
              }}>
                {phaseEditing ? '취소' : '변경'}
              </button>
            )}
          </div>
        </Fade>
        <Fade show={show}>
          <div style={{ marginTop: 8 }}>
            {timeline.map((item, i) => (
              <Fade show={show} delay={i * 50} key={i}>
                <div
                  onClick={phaseEditing ? () => handlePhaseSelect(item.label) : undefined}
                  style={{
                    display: 'flex', gap: 16, position: 'relative',
                    cursor: phaseEditing ? 'pointer' : 'default',
                    borderRadius: 12,
                    outline: phaseEditing && item.status === 'current' ? `2px solid ${theme.primary}` : 'none',
                    padding: phaseEditing ? '4px 6px' : '0',
                    margin: phaseEditing ? '0 -6px' : '0',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => { if (phaseEditing) e.currentTarget.style.background = theme.primaryBg; }}
                  onMouseLeave={e => { if (phaseEditing) e.currentTarget.style.background = 'transparent'; }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 40 }}>
                    <div style={{
                      width: 38, height: 38, borderRadius: 12,
                      background: item.status === 'current' ? theme.primary
                        : item.status === 'done' ? theme.success : theme.primaryLight,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 17, color: item.status === 'upcoming' ? theme.textSub : '#fff',
                      fontWeight: 700, flexShrink: 0,
                    }}>{item.icon}</div>
                    {i < timeline.length - 1 && (
                      <div style={{
                        width: 2, flex: 1, minHeight: 28,
                        background: item.status === 'done' ? theme.success : theme.border,
                      }} />
                    )}
                  </div>
                  <div style={{ flex: 1, paddingBottom: 20, opacity: phaseEditing ? 1 : item.status === 'upcoming' ? 0.6 : 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: 15, fontWeight: 600, color: theme.text }}>{item.label}</span>
                      {item.week && <span style={{ fontSize: 12, color: theme.textSub }}>{item.week}</span>}
                      {!phaseEditing && item.status === 'current' && (
                        <span style={{
                          fontSize: 11, fontWeight: 600, color: theme.primary,
                          background: theme.primaryLight, padding: '3px 10px', borderRadius: 6,
                        }}>현재</span>
                      )}
                      {phaseEditing && item.status === 'current' && (
                        <span style={{
                          fontSize: 11, fontWeight: 600, color: '#fff',
                          background: theme.primary, padding: '3px 10px', borderRadius: 6,
                        }}>현재 설정됨</span>
                      )}
                    </div>
                    {/* 예상 날짜 */}
                    {!phaseEditing && item.day && (user.cycle > 0 || (user.stage === 'ivf' && user.ivfPhase && user.ivfPhase !== 'prep')) && (() => {
                      let estimatedDate;
                      if (item._phaseMatchDay !== undefined) {
                        const today = new Date();
                        today.setHours(0, 0, 0, 0);
                        const dayDiff = item.day - item._phaseMatchDay;
                        estimatedDate = new Date(today);
                        estimatedDate.setDate(estimatedDate.getDate() + dayDiff);
                      } else if (user.periodDate) {
                        estimatedDate = new Date(user.periodDate);
                        estimatedDate.setDate(estimatedDate.getDate() + item.day - 1);
                      }
                      if (!estimatedDate) return null;
                      const isToday = estimatedDate.toDateString() === new Date().toDateString();
                      return (
                        <div style={{ fontSize: 12, color: isToday ? theme.primary : theme.textSub, marginTop: 3, fontWeight: isToday ? 600 : 400 }}>
                          {estimatedDate.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })}{item.status === 'upcoming' ? ' (예상)' : ''}
                        </div>
                      );
                    })()}
                    <div style={{ fontSize: 14, color: theme.textSub, marginTop: 5, lineHeight: 1.6 }}>{item.desc}</div>
                  </div>
                </div>
              </Fade>
            ))}
          </div>
        </Fade>
      </div>
      {phaseToast && (
        <div style={{
          position: 'fixed', bottom: 40, left: '50%', transform: 'translateX(-50%)',
          padding: '12px 28px', borderRadius: 12, background: theme.text,
          color: '#fff', fontSize: 14, fontWeight: 600,
          boxShadow: '0 8px 30px rgba(0,0,0,0.2)', zIndex: 100,
        }}>{phaseToast}</div>
      )}
    </div>
  );
}

// ==================== CHAT ====================
const API_URL = import.meta.env.VITE_API_URL || '';

// 응답 텍스트에서 링크 관련 텍스트 제거 (카드로 대체되므로)
function cleanResponseText(text) {
  if (!text) return text;
  return text
    // 마크다운 링크: [제목](url)
    .replace(/- \[.*?\]\(https?:\/\/.*?\)/g, '')
    // 일반 URL 라인
    .replace(/^.*https?:\/\/\S+.*$/gm, '')
    // "아래 영상을 참고하시면..." 류 안내 문구
    .replace(/아래\s*(영상|블로그|자료).*?(같아요|보세요|드려요|드릴게요)[.!]?/g, '')
    // 연속 빈 줄 정리
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

/** 간단한 인라인 마크다운 → React 엘리먼트 변환 (**bold** 지원) */
function renderInline(text, keyPrefix = '') {
  if (!text) return text;
  // 마크다운 링크 [text](url) + **bold** + 베어 URL 처리
  const regex = /\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|(https?:\/\/[^\s),]+)/g;
  const result = [];
  let lastIndex = 0;
  let idx = 0;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      result.push(text.slice(lastIndex, match.index));
    }
    if (match[1] && match[2]) {
      // [text](url) → 클릭 가능한 링크
      result.push(<a key={`${keyPrefix}a${idx}`} href={match[2]} target="_blank" rel="noopener noreferrer" style={{ color: '#6B4FA0', textDecoration: 'underline', wordBreak: 'break-all' }}>{match[1]}</a>);
    } else if (match[3]) {
      // **bold**
      result.push(<strong key={`${keyPrefix}b${idx}`}>{match[3]}</strong>);
    } else if (match[4]) {
      // 베어 URL (https://...)  → 클릭 가능한 링크
      result.push(<a key={`${keyPrefix}u${idx}`} href={match[4]} target="_blank" rel="noopener noreferrer" style={{ color: '#6B4FA0', textDecoration: 'underline', wordBreak: 'break-all' }}>{match[4]}</a>);
    }
    idx++;
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    result.push(text.slice(lastIndex));
  }
  return result;
}

function renderMarkdown(text) {
  if (!text) return text;
  const lines = text.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 빈 줄
    if (!trimmed) {
      elements.push(<div key={`sp${i}`} style={{ height: 6 }} />);
      i++;
      continue;
    }

    // 헤딩 ### / ## / #
    const headingMatch = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const sizes = { 1: 16, 2: 15, 3: 14 };
      elements.push(
        <div key={`h${i}`} style={{
          fontSize: sizes[level] || 14, fontWeight: 700,
          margin: '10px 0 4px', lineHeight: 1.5,
        }}>{renderInline(headingMatch[2], `h${i}`)}</div>
      );
      i++;
      continue;
    }

    // 리스트 아이템 (-, *, 1.)
    if (/^[-*]\s/.test(trimmed) || /^\d+\.\s/.test(trimmed)) {
      const listItems = [];
      while (i < lines.length) {
        const cur = lines[i].trim();
        if (/^[-*]\s/.test(cur)) {
          listItems.push({ text: cur.replace(/^[-*]\s+/, ''), indent: 0 });
          i++;
        } else if (/^\d+\.\s/.test(cur)) {
          listItems.push({ text: cur.replace(/^\d+\.\s+/, ''), indent: 0 });
          i++;
        } else if (/^\s+[-*]\s/.test(lines[i])) {
          listItems.push({ text: lines[i].trim().replace(/^[-*]\s+/, ''), indent: 1 });
          i++;
        } else {
          break;
        }
      }
      elements.push(
        <div key={`ul${i}`} style={{ margin: '2px 0' }}>
          {listItems.map((item, li) => (
            <div key={li} style={{ paddingLeft: item.indent ? 20 : 6, lineHeight: 1.7, display: 'flex', gap: 6 }}>
              <span style={{ flexShrink: 0 }}>•</span>
              <span>{renderInline(item.text, `li${i}_${li}`)}</span>
            </div>
          ))}
        </div>
      );
      continue;
    }

    // 일반 텍스트
    elements.push(<div key={`p${i}`} style={{ lineHeight: 1.7 }}>{renderInline(trimmed, `p${i}`)}</div>);
    i++;
  }

  return elements;
}

const EXAMPLE_QUESTIONS = [
  '시험관 시작하면 병원을 얼마나 자주 가야 해?',
  '배아 등급이 뭘 의미하는 거야?',
  '시술 하는동안 커피랑 음료는 어떻게 해야해?',
];

export function ChatScreen({ user, uid, pendingMessage, onPendingConsumed, setUser }) {

  const stageInfo = getCurrentStageInfo(user.stage, user.periodDate, user.cycle, user.protocol, user.currentPhase, user.ivfPhase);
  const defaultGreeting = { role: 'ai', text: `안녕하세요, ${user.name}님! 오늘 기분은 어떠신가요? 궁금한 점이 있으면 편하게 물어보세요.`, time: '지금' };
  const [messages, setMessages] = useState([defaultGreeting]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [typingMsg, setTypingMsg] = useState('라일이 생각하고 있어요...');
  const abortRef = useRef(null);
  const [msgFeedback, setMsgFeedback] = useState({});
  const [blogExpanded, setBlogExpanded] = useState({});
  const [show, setShow] = useState(false);
  const isDesktop = typeof window !== 'undefined' && window.innerWidth >= 1024;
  const [sidebarOpen, setSidebarOpen] = useState(isDesktop);
  const [notesOpen, setNotesOpen] = useState(false);
  const [conversations, setConversations] = useState([]); // 대화 목록
  const [chatNotes, setChatNotes] = useState([]);
  const [currentConvId, _setCurrentConvId] = useState(() => localStorage.getItem('lyle_currentConvId') || null);
  const setCurrentConvId = (id) => { _setCurrentConvId(id); if (id) localStorage.setItem('lyle_currentConvId', id); else localStorage.removeItem('lyle_currentConvId'); };
  const [menuOpenId, setMenuOpenId] = useState(null); // 드롭다운 메뉴 열린 대화 ID
  const [renamingId, setRenamingId] = useState(null); // 이름 변경 중인 대화 ID
  const [renameValue, setRenameValue] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const menuRef = useRef(null);
  const scrollRef = useRef(null);
  const searchInputRef = useRef(null);
  useEffect(() => { setShow(true); }, []);
  useEffect(() => { scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight); }, [messages, typing]);

  // 대화 목록 로드
  const loadConversations = async () => {
    if (!uid || user?.isGuest) return;
    try {
      const res = await fetch(`${API_URL}/chat/history/${uid}`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (e) {
      console.error('대화 목록 로드 실패:', e);
    }
  };

  const loadNotes = async () => {
    if (!uid || user?.isGuest) return;
    try {
      const res = await fetch(`${API_URL}/notes/${uid}`);
      if (res.ok) {
        const data = await res.json();
        setChatNotes(data.notes || []);
      }
    } catch (e) {
      console.error('채팅 기억 로드 실패:', e);
    }
  };

  const deleteNote = async (noteId) => {
    try {
      await fetch(`${API_URL}/notes/${uid}/${noteId}`, { method: 'DELETE' });
      setChatNotes(prev => prev.filter(n => n.id !== noteId));
    } catch (e) {
      console.error('채팅 기억 삭제 실패:', e);
    }
  };

  useEffect(() => {
    loadConversations(); loadNotes();
    // localStorage에 저장된 대화가 있으면 복원
    const savedConvId = localStorage.getItem('lyle_currentConvId');
    if (savedConvId && !currentConvId) { loadConversation(savedConvId); }
  }, [uid]);

  // 탭 복귀 시 최신 대화 불러오기 (모바일 앱 전환, 탭 전환 대응)
  useEffect(() => {
    const handleVisibility = () => {
      if (document.visibilityState === 'visible' && currentConvId && !typing) {
        loadConversation(currentConvId);
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [currentConvId, typing]);

  // 진료 체크리스트에서 넘어온 메시지 자동 전송
  useEffect(() => {
    if (pendingMessage && !typing) {
      send(pendingMessage);
      onPendingConsumed?.();
    }
  }, [pendingMessage]);

  // 이전 대화 불러오기
  const loadConversation = async (convId) => {
    try {
      const res = await fetch(`${API_URL}/chat/history/${uid}/${convId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          const loaded = data.messages.map(m => ({
            role: m.role === 'assistant' ? 'ai' : 'user',
            text: m.content,
            links: m.links || [],
            sources: m.sources || [],
            profile_updates: m.profile_updates || {},
            time: '',
          }));
          setMessages([defaultGreeting, ...loaded]);
          setCurrentConvId(convId);
        }
      }
    } catch (e) {
      console.error('대화 불러오기 실패:', e);
    }
    setSidebarOpen(false);
  };

  // 대화 삭제
  const deleteConversation = async (convId) => {
    try {
      await fetch(`${API_URL}/chat/history/${uid}/${convId}`, { method: 'DELETE' });
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (currentConvId === convId) {
        setMessages([defaultGreeting]);
        setCurrentConvId(null);
      }
    } catch (e) {
      console.error('대화 삭제 실패:', e);
    }
    setMenuOpenId(null);
  };

  // 대화 즐겨찾기 토글
  const toggleStar = async (convId, currentStarred) => {
    const newStarred = !currentStarred;
    try {
      await fetch(`${API_URL}/chat/history/${uid}/${convId}/star?starred=${newStarred}`, { method: 'POST' });
      setConversations(prev => prev.map(c =>
        c.id === convId ? { ...c, starred: newStarred } : c
      ));
    } catch (e) {
      console.error('즐겨찾기 실패:', e);
    }
    setMenuOpenId(null);
  };

  // 대화 이름 변경
  const renameConversation = async (convId) => {
    const trimmed = renameValue.trim();
    if (!trimmed) { setRenamingId(null); return; }
    try {
      await fetch(`${API_URL}/chat/history/${uid}/${convId}/rename?title=${encodeURIComponent(trimmed)}`, { method: 'POST' });
      setConversations(prev => prev.map(c =>
        c.id === convId ? { ...c, title: trimmed } : c
      ));
    } catch (e) {
      console.error('이름 변경 실패:', e);
    }
    setRenamingId(null);
  };

  // 드롭다운 외부 클릭 닫기
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpenId(null);
      }
    };
    if (menuOpenId) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpenId]);

  // 새 대화 시작
  const startNewChat = () => {
    setMessages([defaultGreeting]);
    setCurrentConvId(null);
    setSidebarOpen(false);
  };

  const send = async (text) => {
    text = (text || input).trim();
    if (!text || typing) return;
    setInput('');
    const isChecklist = text.startsWith('[진료 체크리스트 완료]');
    const displayText = isChecklist
      ? '✅ ' + text.replace('[진료 체크리스트 완료] ', '')
      : text;
    setMessages(p => [...p, { role: 'user', text: displayText, isSystem: isChecklist, time: '지금' }]);
    setTyping(true);
    setTypingMsg('라일이 생각하고 있어요...');
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uid, message: text, conversation_id: currentConvId }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || '서버 오류');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // 마지막 불완전한 줄은 버퍼에 유지

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'status') {
              setTypingMsg(event.message);
            } else if (event.type === 'response') {
              const data = event;
              setMessages(p => [...p, {
                role: 'ai', text: data.response, links: data.links || [],
                sources: data.sources || [], time: '지금',
                profileUpdates: data.profile_updates || {},
                suggestedReplies: data.suggested_replies || [],
              }]);
              if (data.profile_updates?.fields && setUser) {
                const fields = data.profile_updates.fields;
                setUser(prev => ({
                  ...prev,
                  ...(fields.current_phase && { currentPhase: fields.current_phase }),
                  ...(fields.treatment_stage && { stage: fields.treatment_stage }),
                  ...(fields.treatment_cycle !== undefined && { cycle: fields.treatment_cycle }),
                  ...(fields.protocol && { protocol: fields.protocol }),
                }));
              }
              if (data.conversation_id) setCurrentConvId(data.conversation_id);
              loadConversations();
              loadNotes();
            }
          } catch (_) {}
        }
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        console.log('사용자가 응답을 중단했습니다.');
      } else {
        console.error('Chat API error:', e);
        setMessages(p => [...p, {
          role: 'ai',
          text: '죄송해요, 지금 연결이 불안정해요. 잠시 후 다시 시도해주세요.',
          time: '지금',
        }]);
      }
    } finally {
      abortRef.current = null;
      setTyping(false);
      setTypingMsg('라일이 생각하고 있어요...');
    }
  };

  const stageName = TREATMENT_STAGES.find(s => s.id === user.stage)?.label || '';
  const isFirstMessage = messages.length === 1 && messages[0].role === 'ai';
  const currentConvTitle = currentConvId
    ? (conversations.find(c => c.id === currentConvId)?.title || '대화')
    : '새 대화';

  // Search highlight helper
  const highlightText = (text, keyword) => {
    if (!keyword || !text) return text;
    const parts = String(text).split(new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
    return parts.map((part, idx) =>
      part.toLowerCase() === keyword.toLowerCase()
        ? <mark key={idx} style={{ background: '#FFE082', borderRadius: 2, padding: '0 1px' }}>{part}</mark>
        : part
    );
  };

  // Filter messages based on search keyword
  const filteredMessages = searchKeyword.trim()
    ? messages.filter(msg => msg.text && msg.text.toLowerCase().includes(searchKeyword.toLowerCase()))
    : messages;

  return (
    <div style={{ height: 'calc(100vh - 52px)', display: 'flex', position: 'relative', overflow: 'hidden', fontFamily: "'Noto Sans KR', sans-serif" }}>
      {/* 사이드바 오버레이 - 게스트 모드에서는 숨김 */}
      {!user?.isGuest && sidebarOpen && !isDesktop && (
        <div onClick={() => setSidebarOpen(false)} style={{
          position: 'absolute', inset: 0, background: 'rgba(28,24,38,0.35)',
          zIndex: 20, transition: 'opacity 0.2s', backdropFilter: 'blur(2px)',
        }} />
      )}

      {/* 사이드바 닫혔을 때 햄버거 */}
      {!user?.isGuest && !sidebarOpen && (
        <div style={{ width: 48, paddingTop: 12, borderRight: '1px solid #EAE4F5', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', flexShrink: 0 }}>
          <button onClick={() => setSidebarOpen(true)} style={{
            background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#1C1826', padding: 0, lineHeight: 1,
          }}>☰</button>
        </div>
      )}

      {/* 사이드바 - 데스크톱: 고정, 모바일: 오버레이 */}
      {!user?.isGuest && <div style={{
        position: isDesktop ? 'relative' : 'absolute', left: 0, top: 0, bottom: 0,
        width: 280, minWidth: 280, background: '#FFFFFF', zIndex: 25,
        borderRight: `1px solid #EAE4F5`,
        transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: isDesktop ? 'none' : 'transform 0.25s ease',
        display: sidebarOpen ? 'flex' : 'none', flexDirection: 'column',
      }}>
        <div style={{
          height: 44, padding: '0 16px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontSize: 15, fontWeight: 700, color: '#1C1826' }}>대화 내역</span>
          <button onClick={() => setSidebarOpen(false)} style={{
            background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#6B5F82',
          }}>☰</button>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '10px 12px' }}>
          {/* 새 대화 버튼 */}
          <div onClick={startNewChat} style={{
            padding: '12px 14px', borderRadius: 10, marginBottom: 8, cursor: 'pointer',
            background: '#7B6BC4', color: '#fff', textAlign: 'center',
            transition: 'all 0.15s',
          }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>
              ＋ 새 대화
            </div>
          </div>

          {/* 대화 목록 */}
          {conversations.length > 0 && (
            <div style={{ fontSize: 11, color: theme.textSub, padding: '8px 4px 6px', fontWeight: 600 }}>
              이전 대화
            </div>
          )}
          {/* 즐겨찾기 대화 먼저 */}
          {[...conversations].sort((a, b) => (b.starred ? 1 : 0) - (a.starred ? 1 : 0)).map(conv => (
            <div key={conv.id} onClick={() => loadConversation(conv.id)} style={{
              padding: '10px 14px', borderRadius: 10, marginBottom: 4, cursor: 'pointer',
              background: currentConvId === conv.id ? theme.primaryBg : 'transparent',
              border: currentConvId === conv.id ? `1px solid ${theme.primaryLight}` : '1px solid transparent',
              transition: 'all 0.15s',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              position: 'relative',
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                {renamingId === conv.id ? (
                  <input
                    autoFocus
                    value={renameValue}
                    onChange={e => setRenameValue(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') renameConversation(conv.id); if (e.key === 'Escape') setRenamingId(null); }}
                    onBlur={() => renameConversation(conv.id)}
                    onClick={e => e.stopPropagation()}
                    style={{
                      fontSize: 13, width: '100%', border: `1px solid ${theme.primaryLight}`,
                      borderRadius: 4, padding: '2px 6px', outline: 'none',
                      background: theme.card, color: theme.text,
                    }}
                  />
                ) : (
                  <>
                    <div style={{
                      fontSize: 13, fontWeight: currentConvId === conv.id ? 600 : 400, color: theme.text,
                      whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                    }}>
                      {conv.starred ? '⭐ ' : ''}{conv.title || conv.preview || '대화'}
                    </div>
                    <div style={{ fontSize: 11, color: theme.textSub, marginTop: 2 }}>
                      메시지 {conv.messageCount}개
                    </div>
                  </>
                )}
              </div>
              <button onClick={(e) => { e.stopPropagation(); setMenuOpenId(menuOpenId === conv.id ? null : conv.id); }} style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: theme.textSub, fontSize: 14, padding: '4px 6px',
                borderRadius: 6, flexShrink: 0, marginLeft: 6,
              }}
              onMouseEnter={e => e.target.style.color = theme.text}
              onMouseLeave={e => e.target.style.color = theme.textSub}
              >⋯</button>

              {/* 드롭다운 메뉴 */}
              {menuOpenId === conv.id && (
                <div ref={menuRef} onClick={e => e.stopPropagation()} style={{
                  position: 'absolute', right: 8, top: '100%', zIndex: 50,
                  background: theme.card, border: `1px solid ${theme.border}`,
                  borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  minWidth: 120, overflow: 'hidden',
                }}>
                  <div onClick={() => toggleStar(conv.id, conv.starred)} style={{
                    padding: '8px 14px', fontSize: 13, cursor: 'pointer', color: theme.text,
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = theme.primaryBg}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <span>{conv.starred ? '★' : '☆'}</span>
                    <span>{conv.starred ? '즐겨찾기 해제' : '즐겨찾기'}</span>
                  </div>
                  <div onClick={() => { setRenamingId(conv.id); setRenameValue(conv.title || conv.preview || ''); setMenuOpenId(null); }} style={{
                    padding: '8px 14px', fontSize: 13, cursor: 'pointer', color: theme.text,
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = theme.primaryBg}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <span>✏️</span>
                    <span>이름 변경</span>
                  </div>
                  <div onClick={() => deleteConversation(conv.id)} style={{
                    padding: '8px 14px', fontSize: 13, cursor: 'pointer', color: '#e74c3c',
                    display: 'flex', alignItems: 'center', gap: 8,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = '#FFF0F0'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <span>🗑️</span>
                    <span>삭제</span>
                  </div>
                </div>
              )}
            </div>
          ))}

        </div>
        {/* 채팅 기억 - 하단 접이식 */}
        <div style={{ borderTop: `1px solid #EAE4F5`, padding: '0 12px' }}>
          <button onClick={() => setNotesOpen(p => !p)} style={{
            width: '100%', padding: '12px 4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            background: 'none', border: 'none', cursor: 'pointer',
          }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: theme.text }}>채팅 기억 {chatNotes.length > 0 && `(${chatNotes.length})`}</span>
            <span style={{ fontSize: 12, color: theme.textSub }}>{notesOpen ? '▲' : '▼'}</span>
          </button>
          {notesOpen && (
            <div style={{ paddingBottom: 12, maxHeight: 200, overflow: 'auto' }}>
              {chatNotes.length === 0 ? (
                <div style={{ fontSize: 12, color: theme.textSub, padding: '4px 4px', lineHeight: 1.5 }}>
                  아직 항목이 없어요. 대화하면서 자동으로 추가돼요.
                </div>
              ) : chatNotes.map(note => (
                <div key={note.id} style={{
                  padding: '8px 12px', borderRadius: 8, marginBottom: 3,
                  background: '#F2EFFA', border: `1px solid #EAE4F5`,
                  display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, color: '#1C1826', lineHeight: 1.4 }}>{note.content}</div>
                    <div style={{ fontSize: 10, color: '#6B5F82', marginTop: 3 }}>
                      {note.created_at ? new Date(note.created_at).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) : ''}
                    </div>
                  </div>
                  <button onClick={() => deleteNote(note.id)} style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: '#6B5F82', fontSize: 13, padding: '2px 4px',
                  }}
                  onMouseEnter={e => e.target.style.color = '#e74c3c'}
                  onMouseLeave={e => e.target.style.color = '#6B5F82'}
                  >🗑️</button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>}

      {/* 메인 채팅 영역 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', width: '100%', background: '#F8F6FD' }}>
        {/* 커스텀 탑바 */}
        <div style={{
          height: 44, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 12px', background: '#F8F6FD',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
            <span style={{ fontSize: 15, fontWeight: 600, color: '#1C1826', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{currentConvTitle}</span>
          </div>
          <button onClick={() => { setSearchOpen(!searchOpen); setSearchKeyword(''); }} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 18, color: '#6B5F82', padding: 4, lineHeight: 1,
          }}>🔍</button>
        </div>

        {/* 검색바 */}
        {searchOpen && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '8px 12px', borderBottom: '1px solid #EAE4F5',
            background: '#FFFFFF', flexShrink: 0,
          }}>
            <input
              ref={searchInputRef}
              autoFocus
              value={searchKeyword}
              onChange={e => setSearchKeyword(e.target.value)}
              placeholder="대화 내용 검색..."
              style={{
                flex: 1, padding: '8px 14px', borderRadius: 20,
                border: '1px solid #DDD6F3', background: '#F8F6FD',
                fontSize: 13, outline: 'none', color: '#1C1826',
                fontFamily: "'Noto Sans KR', sans-serif",
              }}
            />
            <button onClick={() => { setSearchOpen(false); setSearchKeyword(''); }} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: 16, color: '#6B5F82', padding: 4,
            }}>✕</button>
          </div>
        )}

        <div ref={scrollRef} className="chat-messages-area" style={{ flex: 1, overflow: 'auto', padding: '16px 60px 20px', background: '#F8F6FD' }}>
          {!searchKeyword && <Fade show={show}>
            <div style={{ textAlign: 'center', padding: '4px 0 18px', fontSize: 12, color: '#6B5F82' }}>
              <span style={{
                background: '#F2EFFA', padding: '5px 14px', borderRadius: 8,
                border: `1px solid #DDD6F3`,
              }}>{user.name}님 · {stageName} {user.cycle === 0 ? ' 준비 중' : ` ${user.cycle}회차`}</span>
            </div>
          </Fade>}

          {filteredMessages.map((msg, i) => {
            const originalIndex = messages.indexOf(msg);
            return (
            <Fade show={show} delay={i * 40} key={originalIndex}>
              <div style={{
                display: 'flex', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                marginBottom: 14, gap: 10, alignItems: 'flex-start',
              }}>
                {msg.role === 'ai' && (
                  <div style={{
                    width: 28, height: 28, borderRadius: 14,
                    background: `linear-gradient(135deg, #7B6BC4, ${theme.accent})`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 13, fontWeight: 700, color: '#fff', flexShrink: 0,
                  }}>L</div>
                )}
                <div style={{ maxWidth: '70%' }}>
                  <div style={{
                    padding: '12px 16px',
                    background: msg.isSystem ? '#F0F7F4' : msg.role === 'user' ? '#7B6BC4' : '#FFFFFF',
                    color: msg.isSystem ? '#1C1826' : msg.role === 'user' ? '#fff' : '#1C1826',
                    fontSize: msg.isSystem ? 13 : 14, lineHeight: 1.6, whiteSpace: msg.role === 'ai' ? 'normal' : 'pre-line',
                    border: msg.isSystem ? '1px solid #DDD6F3' : msg.role === 'ai' ? '1px solid #EAE4F5' : 'none',
                    borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                    boxShadow: msg.role === 'user' ? '0 2px 12px rgba(123,107,196,.3)' : 'none',
                  }}>{msg.role === 'ai'
                    ? (searchKeyword
                      ? highlightText(msg.links && msg.links.length > 0 ? cleanResponseText(msg.text) : msg.text, searchKeyword)
                      : renderMarkdown(msg.links && msg.links.length > 0 ? cleanResponseText(msg.text) : msg.text))
                    : (searchKeyword ? highlightText(msg.text, searchKeyword) : msg.text)
                  }</div>
                  {msg.links && msg.links.length > 0 && (() => {
                    const youtubeLinks = msg.links.filter(l => l.source_type === 'youtube');
                    const blogLinks = msg.links.filter(l => l.source_type === 'blog');
                    return (
                      <div>
                        {/* 유튜브 카드 */}
                        {youtubeLinks.length > 0 && (
                          <div style={{
                            display: 'flex', gap: 10, overflowX: 'auto', paddingTop: 6, paddingBottom: 4,
                            scrollSnapType: 'x mandatory', WebkitOverflowScrolling: 'touch',
                          }}>
                            {youtubeLinks.map((link, li) => (
                              <a key={li} href={link.url} target="_blank" rel="noopener noreferrer" style={{
                                flex: '0 0 220px', scrollSnapAlign: 'start', textDecoration: 'none',
                                borderRadius: 12, overflow: 'hidden',
                                border: `1px solid ${theme.border}`, background: theme.card,
                              }}>
                                <div style={{
                                  width: '100%', height: 120, background: '#000',
                                  backgroundImage: `url(https://img.youtube.com/vi/${link.video_id}/mqdefault.jpg)`,
                                  backgroundSize: 'cover', backgroundPosition: 'center',
                                  position: 'relative',
                                }}>
                                  <div style={{
                                    position: 'absolute', inset: 0, display: 'flex',
                                    alignItems: 'center', justifyContent: 'center',
                                  }}>
                                    <div style={{
                                      width: 40, height: 40, borderRadius: 20, background: 'rgba(0,0,0,0.6)',
                                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                                      color: '#fff', fontSize: 18,
                                    }}>▶</div>
                                  </div>
                                </div>
                                <div style={{ padding: '10px 12px' }}>
                                  <div style={{ fontSize: 12, color: theme.textSub, marginBottom: 4 }}>
                                    📺 {link.channel || '전문 의료진 YouTube'}
                                  </div>
                                  <div style={{
                                    fontSize: 13, fontWeight: 500, color: theme.text,
                                    overflow: 'hidden', textOverflow: 'ellipsis',
                                    display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                                  }}>{link.title}</div>
                                </div>
                              </a>
                            ))}
                          </div>
                        )}
                        {/* 블로그 버튼은 suggestion 라인으로 이동됨 */}
                      </div>
                    );
                  })()}
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ fontSize: 11, color: theme.textSub, marginTop: 6, paddingLeft: 2 }}>
                      출처: {msg.sources.join(' · ')}
                    </div>
                  )}
                  {/* 예시 답변 카드 + 블로그 버튼 (같은 라인) */}
                  {msg.role === 'ai' && ((msg.suggestedReplies && msg.suggestedReplies.length > 0) || ((() => { const bl = (msg.links || []).filter(l => l.source_type === 'blog'); return bl.length > 0; })())) && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
                      {msg.suggestedReplies && msg.suggestedReplies.map((reply, ri) => (
                        <button key={ri} onClick={() => send(reply)} style={{
                          background: '#F2EFFA',
                          border: '1px solid #DDD6F3',
                          borderRadius: 20, padding: '7px 16px',
                          fontSize: 13, color: '#7B6BC4',
                          cursor: 'pointer', transition: 'all 0.15s',
                          fontWeight: 500, fontFamily: "'Noto Sans KR', sans-serif",
                        }}>
                          {reply}
                        </button>
                      ))}
                      {/* 블로그 경험담 버튼 - suggestion과 같은 라인 */}
                      {(() => {
                        const blogLinks = (msg.links || []).filter(l => l.source_type === 'blog');
                        if (blogLinks.length === 0) return null;
                        return (
                          <button onClick={() => setBlogExpanded(prev => ({ ...prev, [i]: !prev[i] }))} style={{
                            background: theme.primaryBg, border: `1px solid ${theme.primaryLight}`,
                            borderRadius: 20, padding: '7px 16px', fontSize: 13,
                            color: theme.primary, fontWeight: 500, cursor: 'pointer',
                          }}>
                            {blogExpanded[i] ? '접기 ↑' : '비슷한 경험 보기 💜'}
                          </button>
                        );
                      })()}
                    </div>
                  )}
                  {/* 블로그 펼침 영역 */}
                  {blogExpanded[i] && (() => {
                    const blogLinks = (msg.links || []).filter(l => l.source_type === 'blog');
                    if (blogLinks.length === 0) return null;
                    return (
                      <div style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingTop: 8, paddingBottom: 4, scrollSnapType: 'x mandatory' }}>
                        {blogLinks.map((link, li) => (
                          <a key={li} href={link.url} target="_blank" rel="noopener noreferrer" style={{
                            flex: '0 0 220px', scrollSnapAlign: 'start', textDecoration: 'none',
                            borderRadius: 12, overflow: 'hidden',
                            border: `1px solid ${theme.border}`, background: theme.card,
                            padding: '12px 14px', display: 'block',
                          }}>
                            <div style={{ fontSize: 12, color: theme.textSub, marginBottom: 4 }}>📝 경험담</div>
                            <div style={{
                              fontSize: 13, fontWeight: 500, color: theme.text,
                              overflow: 'hidden', textOverflow: 'ellipsis',
                              display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                            }}>{link.title}</div>
                          </a>
                        ))}
                      </div>
                    );
                  })()}
                  {/* 피드백 버튼 (봇 메시지만) */}
                  {msg.role === 'ai' && (
                    <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
                      {['👍', '👎'].map(emoji => {
                        const type = emoji === '👍' ? 'up' : 'down';
                        const selected = msgFeedback[i] === type;
                        return (
                          <button key={type} onClick={() => {
                            const newVal = msgFeedback[i] === type ? null : type;
                            setMsgFeedback(prev => ({ ...prev, [i]: newVal }));
                            if (newVal) {
                              const prevUserMsg = messages.slice(0, i).reverse().find(m => m.role === 'user');
                              fetch('/feedback', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                  uid,
                                  rating: newVal,
                                  user_message: prevUserMsg?.text || '',
                                  bot_response: msg.text || '',
                                  conversation_id: currentConvId || '',
                                }),
                              }).catch(() => {});
                            }
                          }} style={{
                            background: selected ? (type === 'up' ? '#EEF0FF' : '#FFF0F0') : 'transparent',
                            border: `1px solid ${selected ? (type === 'up' ? theme.primary : '#E88') : theme.border}`,
                            borderRadius: 8, padding: '3px 8px', fontSize: 14,
                            cursor: 'pointer', transition: 'all 0.15s',
                          }}>{emoji}</button>
                        );
                      })}
                    </div>
                  )}
                  {/* 기록됨 카드 - 게스트 모드에서는 숨김 */}
                  {!user?.isGuest && msg.profileUpdates && (
                    (msg.profileUpdates.fields && Object.keys(msg.profileUpdates.fields).length > 0) ||
                    (msg.profileUpdates.notes && msg.profileUpdates.notes.length > 0)
                  ) && (() => {
                    const items = [];
                    const fieldLabels = {
                      treatment_stage: '시술 단계', current_phase: '현재 단계', protocol: '프로토콜',
                      treatment_cycle: '시술 회차', amh: 'AMH', diagnoses: '진단명',
                      infertility_duration: '난임 기간', marriage_status: '혼인 상태',
                      dual_income: '맞벌이', partner_diagnosis: '배우자 진단',
                      frozen_embryo_count: '동결배아 수', current_medications: '복용 약물',
                      embryo_grade: '배아 등급',
                    };
                    if (msg.profileUpdates.fields) {
                      Object.entries(msg.profileUpdates.fields).forEach(([k, v]) => {
                        items.push(`${fieldLabels[k] || k}: ${Array.isArray(v) ? v.join(', ') : v}`);
                      });
                    }
                    if (msg.profileUpdates.notes) {
                      msg.profileUpdates.notes.forEach(n => items.push(n));
                    }
                    if (items.length === 0) return null;
                    return (
                      <div style={{
                        marginTop: 10, padding: '10px 14px', borderRadius: 10,
                        background: '#F0F7F4', border: `1px solid ${theme.primaryLight}`,
                      }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: theme.primary, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span>📋</span> 기록됨
                        </div>
                        {items.map((item, idx) => (
                          <div key={idx} style={{ fontSize: 12, color: theme.text, lineHeight: 1.5 }}>
                            {items.length > 1 ? `${idx + 1}. ${item}` : item}
                          </div>
                        ))}
                        <div style={{ fontSize: 10, color: theme.textSub, marginTop: 6 }}>
                          핵심 의료 정보는 정확도를 위해 별도 기록 및 관리됩니다.
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </div>
            </Fade>
          );
          })}

          {/* 예시 질문 (첫 메시지일 때만) */}
          {isFirstMessage && !typing && !searchKeyword && (
            <Fade show={show} delay={200}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8, marginBottom: 14 }}>
                {EXAMPLE_QUESTIONS.map((q, i) => (
                  <button key={i} onClick={() => send(q)} style={{
                    padding: '8px 16px', borderRadius: 20,
                    border: '1px solid #DDD6F3', background: '#F2EFFA',
                    color: '#7B6BC4', fontSize: 12, fontWeight: 500,
                    cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.2s',
                    fontFamily: "'Noto Sans KR', sans-serif",
                  }}>{q}</button>
                ))}
              </div>
            </Fade>
          )}

          {/* 게스트 회원가입 유도 카드 — 유저 메시지 3개 이상일 때 한 번만 */}
          {user?.isGuest && messages.filter(m => m.role === 'user').length >= 3 && (
            <div style={{
              margin: '12px auto 16px', maxWidth: 480, padding: '16px 20px',
              background: `linear-gradient(135deg, ${theme.primaryBg}, ${theme.primaryLight}40)`,
              border: `1px solid ${theme.primaryLight}`, borderRadius: 14, textAlign: 'center',
            }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: theme.text, marginBottom: 6 }}>
                계정을 등록하면 더 맞춤형 대화가 가능해요
              </div>
              <div style={{ fontSize: 12, color: theme.textSub, marginBottom: 12, lineHeight: 1.5 }}>
                시술 단계, 복용 약물, 진료 기록을 기반으로 나에게 딱 맞는 정보를 받을 수 있어요.
              </div>
              <button onClick={onStartOnboarding} style={{
                padding: '8px 20px', borderRadius: 10, border: 'none', cursor: 'pointer',
                background: theme.primary, color: '#fff', fontSize: 13, fontWeight: 600,
              }}>계정 등록하기</button>
            </div>
          )}

          {typing && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14 }}>
              <div style={{
                width: 28, height: 28, borderRadius: 14,
                background: `linear-gradient(135deg, #7B6BC4, ${theme.accent})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 13, fontWeight: 700, color: '#fff',
              }}>L</div>
              <div style={{
                padding: '12px 16px', borderRadius: '4px 16px 16px 16px', background: '#FFFFFF',
                border: '1px solid #EAE4F5', fontSize: 14, color: '#6B5F82',
              }}>{typingMsg}</div>
            </div>
          )}
        </div>

        <div style={{
          padding: '10px 12px 14px', borderTop: '1px solid #EAE4F5',
          background: '#FFFFFF', display: 'flex', gap: 10, alignItems: 'center',
        }}>
          <input value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.nativeEvent.isComposing && send()}
            placeholder="라일에게 무엇이든 물어보세요"
            disabled={typing}
            style={{
              flex: 1, padding: '11px 20px', borderRadius: 24,
              border: '1px solid #EAE4F5', background: '#F8F6FD',
              fontSize: 14, outline: 'none', color: '#1C1826',
              opacity: typing ? 0.6 : 1,
              fontFamily: "'Noto Sans KR', sans-serif",
            }} />
          <button onClick={() => {
            if (typing && abortRef.current) {
              abortRef.current.abort();
            } else {
              send();
            }
          }} style={{
            width: 40, height: 40, borderRadius: 20,
            background: typing ? '#E05C6B' : '#7B6BC4', color: '#fff', border: 'none',
            cursor: 'pointer', fontSize: 18,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0, lineHeight: 1,
          }}>{typing ? '■' : '↑'}</button>
        </div>
      </div>
    </div>
  );
}

// ==================== CALC ====================
export function CalcScreen({ user, uid, setUser, setTab, onStartOnboarding }) {
  const isGuest = uid?.startsWith('guest_');
  if (isGuest) return (
    <div className="page-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 24px', background: '#F8F6FD' }}>
      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>지원금 확인</div>
      <div style={{ fontSize: 14, color: '#8C82A6', marginBottom: 24, lineHeight: 1.6, textAlign: 'center' }}>맞춤형 지원금 정보를 확인하려면<br/>계정 등록이 필요해요.</div>
      <button onClick={onStartOnboarding} style={{
        padding: '12px 32px', borderRadius: 12, border: 'none', cursor: 'pointer',
        background: '#7C6AAF', color: '#fff', fontSize: 15, fontWeight: 600,
      }}>계정 등록하기</button>
    </div>
  );

  const [show, setShow] = useState(false);
  const [subsidy, setSubsidy] = useState(null);
  const [loading, setLoading] = useState(false);
  const married = user?.marriageStatus || null;
  useEffect(() => { setShow(true); }, []);

  const handleMarriageSelect = async (value) => {
    setUser(prev => ({ ...prev, marriageStatus: value }));
    if (uid) {
      try { await saveUserProfile(uid, { marriageStatus: value }); }
      catch (e) { console.error('marriageStatus 저장 실패:', e); }
    }
  };

  // 프로필 기반 로컬 계산 (fallback)
  const calcLocal = () => {
    const stageId = user?.stage || 'prep';
    const cycle = parseInt(user?.cycle || 0);
    const STAGE_LABELS = {
      prep: '임신 준비', testing: '난임 검사', iui: '인공수정 (IUI)',
      ivf: '체외수정 (IVF)', fet: '동결배아 이식 (FET)', retry: '재시도',
    };
    const AMOUNTS = { iui: 300000, ivf: 1100000, fet: 500000 };
    const MAX_SESSIONS = { iui: 5, ivf: 20, fet: 20 };
    const NAMES = { iui: '인공수정', ivf: '체외수정 (신선배아)', fet: '동결배아 이식' };
    const key = ['iui', 'ivf', 'fet'].includes(stageId) ? stageId : 'ivf';
    const perSession = AMOUNTS[key];
    const maxSessions = MAX_SESSIONS[key];
    const remaining = Math.max(0, maxSessions - cycle);
    const perDisplay = `최대 ${perSession / 10000}만원`;
    return {
      eligible: married === 'legal' || married === 'defacto',
      marriageStatus: married,
      stage: STAGE_LABELS[stageId] || stageId,
      region: [user?.region1, user?.region2].filter(Boolean).join(' '),
      totalEstimate: perDisplay,
      perSession: perDisplay,
      cards: [
        { label: '건강보험 적용', value: '본인부담 30%', sub: '연령 무관 일괄 적용 (2024.11~)' },
        { label: '정부 난임시술 지원금', value: `회당 ${perDisplay}`, sub: `${NAMES[key]} 기준 · 통지서 발급 필수`, link: 'https://www.gov.kr/search/apply?query=%EB%82%9C%EC%9E%84' },
        { label: '지원 횟수', value: `최대 ${maxSessions}회`, sub: `출산당 기준 (${NAMES[key]})` },
        { label: '난임치료 휴가', value: '연 6일', sub: '최초 2일 유급 (근로기준법)' },
      ],
      notice: '시술 시작 전에 보건소 지원결정통지서를 반드시 발급받으세요. 소급 지원이 불가합니다.',
      source: '2026년 모자보건사업 안내',
    };
  };

  // 혼인 여부 선택 후 API 호출 (실패 시 로컬 계산)
  useEffect(() => {
    if (!married) return;
    if (!uid) { setSubsidy(calcLocal()); return; }
    setLoading(true);
    fetch(`${API_URL}/subsidy/${uid}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => setSubsidy(data || calcLocal()))
      .catch(() => setSubsidy(calcLocal()))
      .finally(() => setLoading(false));
  }, [married, uid]);

  const CARD_COLORS = ['#8B6CC1', '#A084D0', '#B49CDE', '#C7B3EC'];

  if (married === null) return (
    <div className="page-content" style={{ flex: 1, overflow: 'auto', padding: '0 24px 40px' }}>
      <Header title="지원금 확인" subtitle="추가 정보가 필요해요" />
      <div style={{ width: '100%' }}>
        <Fade show={show}>
          <p style={{ fontSize: 15, color: theme.textSub, margin: '20px 0 24px', lineHeight: 1.7 }}>
            지원금 자격을 확인하려면 혼인 여부 정보가 필요해요.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { v: 'legal', l: '법적 혼인', d: '혼인신고 완료' },
              { v: 'defacto', l: '사실혼', d: '1년 이상 사실혼 관계' },
              { v: 'none', l: '미혼 / 해당없음', d: '' },
            ].map(m => (
              <button key={m.v} onClick={() => handleMarriageSelect(m.v)} style={{
                padding: '18px 22px', borderRadius: theme.radius,
                border: `1.5px solid ${theme.border}`, background: theme.card,
                cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s',
              }}>
                <div style={{ fontSize: 15, fontWeight: 600, color: theme.text }}>{m.l}</div>
                {m.d && <div style={{ fontSize: 13, color: theme.textSub, marginTop: 3 }}>{m.d}</div>}
              </button>
            ))}
          </div>
        </Fade>
      </div>
    </div>
  );

  if (loading || !subsidy) return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ color: theme.textSub, fontSize: 15 }}>지원금 정보를 불러오는 중...</div>
    </div>
  );

  return (
    <div className="page-content" style={{ flex: 1, overflow: 'auto', padding: '0 24px 40px' }}>
      <Header title="지원금" subtitle={subsidy.region ? `${subsidy.region} · ${subsidy.stage}` : subsidy.stage} />
      <div style={{ maxWidth: 960, margin: "0 auto" }}>

        {/* 자격 미달 (미혼) */}
        {!subsidy.eligible && (
          <Fade show={show}>
            <div style={{
              background: '#FFF5F5', border: '1px solid #FED7D7', borderRadius: 16,
              padding: 24, marginTop: 16, marginBottom: 20,
            }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#C53030', marginBottom: 8 }}>
                정부 난임시술비 지원 대상이 아닙니다
              </div>
              <div style={{ fontSize: 13, color: '#9B2C2C', lineHeight: 1.7 }}>
                난임부부 시술비 지원은 법적 혼인 또는 사실혼 관계인 부부를 대상으로 합니다.
                다만 건강보험 급여 적용은 혼인 여부와 관계없이 가능하며,
                임신 사전건강관리 지원(AMH 검사 등)도 별도로 받으실 수 있어요.
              </div>
            </div>
          </Fade>
        )}

        {/* 예상 지원금 요약 */}
        {subsidy.eligible && (
          <Fade show={show}>
            <div style={{
              background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 100%)`,
              borderRadius: 18, padding: 28, marginTop: 16, marginBottom: 20, color: '#fff',
            }}>
              <div style={{ fontSize: 13, opacity: 0.8 }}>정부 난임시술비 지원금</div>
              <div style={{ fontSize: 32, fontWeight: 800, marginTop: 8 }}>{subsidy.perSession}</div>
              <button onClick={() => setTab && setTab('chat')} style={{
                marginTop: 16, padding: '10px 20px', borderRadius: 10, border: 'none', cursor: 'pointer',
                background: 'rgba(255,255,255,0.2)', color: '#fff', fontSize: 13, fontWeight: 600,
                backdropFilter: 'blur(4px)',
              }}>AI 상담에서 자세히 알아보기 →</button>
            </div>
          </Fade>
        )}

        {/* 상세 카드 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {subsidy.cards.map((card, i) => (
            <Fade show={show} delay={i * 60} key={i}>
              <div onClick={() => card.link && window.open(card.link, '_blank')} style={{
                padding: 20, borderRadius: theme.radius,
                border: `1px solid ${theme.border}`, background: theme.card,
                cursor: card.link ? 'pointer' : 'default',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: 13, color: theme.textSub }}>{card.label}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: theme.text, marginTop: 5 }}>{card.value}</div>
                  </div>
                  <div style={{ width: 10, height: 10, borderRadius: 5, background: CARD_COLORS[i % 4], marginTop: 4 }} />
                </div>
                {card.sub && <div style={{ fontSize: 12, color: theme.textSub, marginTop: 8 }}>{card.sub}</div>}
                {card.link && <div style={{ fontSize: 11, color: theme.primary, marginTop: 6 }}>클릭하여 신청 →</div>}
              </div>
            </Fade>
          ))}
        </div>

        {/* 주의사항 */}
        <Fade show={show} delay={300}>
          <div style={{
            padding: '16px 20px', borderRadius: 12, background: '#FFFBF0',
            border: '1px solid #F0E6CC', marginTop: 14,
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#9E8B5E', marginBottom: 5 }}>
              {'\u26A0\uFE0F'} 꼭 기억하세요
            </div>
            <div style={{ fontSize: 13, color: '#8B7A4E', lineHeight: 1.7 }}>{subsidy.notice}</div>
          </div>
        </Fade>

        {/* AI 상담 유도 — 히어로 카드에 통합됨 */}

        {/* 출처 */}
        <div style={{ fontSize: 11, color: theme.textSub, marginTop: 12, opacity: 0.6, textAlign: 'right' }}>
          출처: {subsidy.source}
        </div>
      </div>
    </div>
  );
}

// ==================== RECORDS (기록) ====================
export function RecordsScreen({ user, uid, onStartOnboarding }) {
  const isGuest = user?.isGuest;
  const [show, setShow] = useState(false);
  const [records, setRecords] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addForm, setAddForm] = useState({ category: '', content: '', date: new Date().toISOString().split('T')[0] });
  const [calMonth, setCalMonth] = useState(() => { const d = new Date(); return { year: d.getFullYear(), month: d.getMonth() }; });
  const [selectedDay, setSelectedDay] = useState(null);

  useEffect(() => { setShow(true); }, []);

  const categories = [
    { id: '생리시작일', icon: '🩸' },
    { id: '영양제', icon: '💊' },
    { id: '증상', icon: '🌡️' },
    { id: '체중', icon: '⚖️' },
    { id: '병원', icon: '🏨' },
  ];

  // Firebase에서 records 로드
  useEffect(() => {
    if (!uid || uid.startsWith('guest_')) return;
    const loadRecords = async () => {
      try {
        const res = await fetch(`/records/${uid}`);
        if (res.ok) {
          const data = await res.json();
          setRecords(data.records || []);
        }
      } catch {}
    };
    loadRecords();
  }, [uid]);

  if (isGuest) {
    return (
      <div className="page-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 24px', background: '#F8F6FD' }}>
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>나의 기록</div>
        <div style={{ fontSize: 14, color: '#8C82A6', marginBottom: 24, lineHeight: 1.6, textAlign: 'center' }}>맞춤형 기록 관리를 이용하려면<br/>계정 등록이 필요해요.</div>
        <button onClick={onStartOnboarding} style={{
          padding: '12px 32px', borderRadius: 12, border: 'none', cursor: 'pointer',
          background: '#7C6AAF', color: '#fff', fontSize: 15, fontWeight: 600,
        }}>계정 등록하기</button>
      </div>
    );
  }

  const addRecord = async () => {
    if (!addForm.category) return;
    const content = addForm.content.trim() || addForm.category;
    const newRecord = {
      id: Date.now(),
      category: addForm.category,
      content,
      date: addForm.date,
    };
    setRecords(prev => [newRecord, ...prev]);
    try {
      await fetch(`/records/${uid}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newRecord),
      });
    } catch {}
    if (addForm.category === '생리시작일') {
      try { await saveUserProfile(uid, { periodDate: addForm.date }); } catch {}
    }
    setAddForm({ category: '', content: '', date: new Date().toISOString().split('T')[0] });
    setShowAddModal(false);
  };

  const daysInMonth = new Date(calMonth.year, calMonth.month + 1, 0).getDate();
  const firstDayOfWeek = new Date(calMonth.year, calMonth.month, 1).getDay();
  const today = new Date();

  const recordsForDay = (day) => records.filter(r => {
    const d = new Date(r.date + 'T00:00');
    return d.getFullYear() === calMonth.year && d.getMonth() === calMonth.month && d.getDate() === day;
  });

  return (
    <div className="page-content" style={{ flex: 1, overflow: 'auto', padding: '0 20px 40px' }}>
      {/* Header */}
      <div style={{
        padding: '16px 0 8px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: theme.text, letterSpacing: -0.3 }}>나의 기록</div>
          <div style={{ fontSize: 13, color: theme.textSub, marginTop: 3, marginBottom: 6 }}>라일이 저장하거나 직접 추가해요</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button onClick={() => setShowAddModal(true)} style={{
            width: 36, height: 36, borderRadius: '50%', border: 'none',
            background: theme.primary, color: '#fff', cursor: 'pointer', fontSize: 22,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 12px rgba(123,107,196,0.35)',
          }}>+</button>
        </div>
      </div>

      {/* Calendar */}
      <div className="calendar-card" style={{
        background: theme.card, borderRadius: 18, padding: 18,
        boxShadow: '0 1px 8px rgba(123,107,196,0.08)',
        maxWidth: 640, margin: '0 auto',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: theme.text }}>
            {calMonth.year}년 {calMonth.month + 1}월
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            {['◀', '▶'].map((arrow, i) => (
              <button key={i} onClick={() => {
                setCalMonth(p => {
                  const m = i === 0 ? p.month - 1 : p.month + 1;
                  return { month: m < 0 ? 11 : m > 11 ? 0 : m, year: m < 0 ? p.year - 1 : m > 11 ? p.year + 1 : p.year };
                });
                setSelectedDay(null);
              }} style={{
                width: 28, height: 28, borderRadius: 8, border: `1px solid ${theme.border}`,
                background: theme.card, cursor: 'pointer', fontSize: 11, color: theme.textSub,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>{arrow}</button>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2 }}>
          {['일','월','화','수','목','금','토'].map(d => (
            <div key={d} style={{ textAlign: 'center', fontSize: 11, fontWeight: 600, color: theme.textSub, padding: '6px 0' }}>{d}</div>
          ))}
          {Array(firstDayOfWeek).fill(null).map((_, i) => <div key={`e${i}`} />)}
          {Array.from({ length: daysInMonth }, (_, i) => i + 1).map(day => {
            const isToday = today.getFullYear() === calMonth.year && today.getMonth() === calMonth.month && today.getDate() === day;
            const hasRec = recordsForDay(day).length > 0;
            const isSel = selectedDay === day;
            return (
              <button key={day} onClick={() => { setSelectedDay(isSel ? null : day); const ds = `${calMonth.year}-${String(calMonth.month+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`; setAddForm(prev => ({...prev, date: ds})); }} style={{
                height: 44, borderRadius: '50%', border: 'none',
                background: isSel ? theme.primary : isToday ? theme.primaryLight : 'transparent',
                color: isSel ? '#fff' : isToday ? theme.primary : theme.textSub,
                fontSize: 12.5, fontWeight: isToday || isSel ? 700 : 400,
                cursor: 'pointer', position: 'relative',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1,
              }}>
                {day}
                {hasRec && <div style={{
                  width: 4, height: 4, borderRadius: '50%',
                  background: isSel ? '#fff' : '#C0B2E8',
                }} />}
              </button>
            );
          })}
        </div>

        {/* Legend */}
        <div style={{
          display: 'flex', gap: 12, marginTop: 14, paddingTop: 12,
          borderTop: `1px solid ${theme.border}`, flexWrap: 'wrap',
        }}>
          {[
            { color: theme.primaryLight, border: `1.5px solid ${theme.primary}`, label: '오늘' },
            { color: '#C0B2E8', label: '기록 있음' },
          ].map((l, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: theme.textSub }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: l.color, border: l.border || 'none' }} />
              {l.label}
            </div>
          ))}
        </div>
      </div>

      {/* Selected day panel */}
      {selectedDay !== null && (
        <div style={{ marginTop: 12, maxWidth: 680, margin: '12px auto 0' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, padding: '0 2px' }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: theme.text }}>
              {calMonth.month + 1}월 {selectedDay}일
            </span>
            <button onClick={() => setSelectedDay(null)} style={{
              fontSize: 12, color: theme.textSub, background: 'none', border: 'none', cursor: 'pointer',
            }}>닫기</button>
          </div>
          {recordsForDay(selectedDay).length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px 0', color: theme.textSub, fontSize: 13 }}>
              이 날의 기록이 없어요
            </div>
          ) : (
            <div style={{ position: 'relative', paddingLeft: 20 }}>
              <div style={{ position: 'absolute', left: 7, top: 6, bottom: 6, width: 2, background: theme.border, borderRadius: 1 }} />
              {recordsForDay(selectedDay).map(r => {
                const cat = categories.find(c => c.id === r.category);
                return (
                  <div key={r.id} style={{ display: 'flex', gap: 10, marginBottom: 12, position: 'relative' }}>
                    <div style={{
                      width: 8, height: 8, borderRadius: '50%', background: theme.primary,
                      position: 'absolute', left: -17, top: 6,
                    }} />
                    <div style={{
                      background: theme.card, borderRadius: 10, border: `1px solid ${theme.border}`,
                      padding: '10px 14px', flex: 1,
                      display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                    }}>
                      <div>
                        <div style={{ fontSize: 12, color: theme.primary, fontWeight: 600, marginBottom: 2 }}>
                          {cat ? `${cat.icon} ${cat.id}` : r.category}
                        </div>
                        <div style={{ fontSize: 13, color: theme.text }}>{r.content}</div>
                      </div>
                      <button onClick={async () => { setRecords(prev => prev.filter(x => x.id !== r.id)); try { await fetch(`/records/${uid}/${r.id}`, { method: 'DELETE' }); } catch {} }} style={{
                        background: 'none', border: 'none', cursor: 'pointer',
                        color: theme.textSub, fontSize: 13, padding: '2px 4px', flexShrink: 0,
                      }}
                      onMouseEnter={e => e.target.style.color = '#e74c3c'}
                      onMouseLeave={e => e.target.style.color = theme.textSub}
                      >🗑️</button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Add record - bottom sheet modal */}
      {showAddModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(28,24,38,0.4)', zIndex: 200,
          display: 'flex', alignItems: 'flex-end',
        }} onClick={() => setShowAddModal(false)}>
          <div style={{
            width: '100%', background: theme.card,
            borderRadius: '24px 24px 0 0', padding: 0,
            maxHeight: '85vh', display: 'flex', flexDirection: 'column',
            animation: 'slideUp 0.25s ease',
          }} onClick={e => e.stopPropagation()}>
            {/* Handle */}
            <div style={{ width: 36, height: 4, borderRadius: 2, background: theme.border, margin: '12px auto 0' }} />
            {/* Header */}
            <div style={{ padding: '16px 20px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 17, fontWeight: 600, color: theme.text }}>기록 추가하기</span>
              <button onClick={() => setShowAddModal(false)} style={{
                width: 32, height: 32, borderRadius: '50%', background: theme.primaryLight,
                border: 'none', cursor: 'pointer', fontSize: 16,
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: theme.textSub,
              }}>✕</button>
            </div>
            {/* Body */}
            <div style={{ padding: '0 20px 20px', overflowY: 'auto' }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: theme.textSub, letterSpacing: 0.5, marginBottom: 10 }}>카테고리 선택</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                {categories.map(cat => (
                  <button key={cat.id} onClick={() => setAddForm(f => ({ ...f, category: cat.id }))} style={{
                    fontSize: 13, fontWeight: 500, padding: '7px 14px', borderRadius: 20,
                    border: `1.5px solid ${addForm.category === cat.id ? theme.primary : theme.border}`,
                    background: addForm.category === cat.id ? theme.primary : theme.card,
                    color: addForm.category === cat.id ? '#fff' : theme.textSub,
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}>{cat.icon} {cat.id}</button>
                ))}
              </div>
              <div style={{ fontSize: 12, fontWeight: 600, color: theme.textSub, letterSpacing: 0.5, marginBottom: 10, marginTop: 16 }}>내용</div>
              <textarea
                value={addForm.content}
                onChange={e => setAddForm(f => ({ ...f, content: e.target.value }))}
                rows={3}
                placeholder="기록할 내용을 입력하세요"
                style={{
                  width: '100%', padding: '13px 16px', borderRadius: 12,
                  border: `1.5px solid ${theme.border}`, background: theme.bg,
                  fontSize: 14, color: theme.text, outline: 'none', resize: 'none', lineHeight: 1.5,
                  boxSizing: 'border-box',
                }}
              />
              <div style={{ fontSize: 12, fontWeight: 600, color: theme.textSub, letterSpacing: 0.5, marginBottom: 10, marginTop: 16 }}>날짜</div>
              <input type="date" value={addForm.date}
                onChange={e => setAddForm(f => ({ ...f, date: e.target.value }))}
                style={{
                  width: '100%', padding: '13px 16px', borderRadius: 12,
                  border: `1.5px solid ${theme.border}`, background: theme.bg,
                  fontSize: 14, color: theme.text, outline: 'none', cursor: 'pointer',
                  boxSizing: 'border-box',
                }}
              />
              <button onClick={addRecord} disabled={!addForm.category} style={{
                width: '100%', padding: 15, marginTop: 16,
                background: theme.primary, color: '#fff', border: 'none', borderRadius: 14,
                fontSize: 15, fontWeight: 600, cursor: 'pointer',
                opacity: addForm.category ? 1 : 0.3,
              }}>저장하기</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== DIARY ====================
export function DiaryScreen() {
  const [show, setShow] = useState(false);
  useEffect(() => { setShow(true); }, []);

  return (
    <div className="page-content" style={{ flex: 1, overflow: 'auto', padding: '0 24px 40px' }}>
      <Header title="감정일기" subtitle="서비스 준비 중" />
      <div style={{ maxWidth: 960, margin: "0 auto" }}>
        <Fade show={show}>
          <div style={{
            padding: '60px 32px', borderRadius: 18, marginTop: 40,
            border: `1px solid ${theme.border}`, background: theme.card,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 52, marginBottom: 20 }}>💜</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: theme.text, marginBottom: 12 }}>
              준비 중이에요
            </div>
            <div style={{ fontSize: 15, color: theme.textSub, lineHeight: 1.8 }}>
              감정일기 기능을 열심히 준비하고 있어요.<br />
              곧 만나볼 수 있으니 조금만 기다려주세요!
            </div>
          </div>
        </Fade>
      </div>
    </div>
  );
}

// ==================== MY PAGE ====================
export function MyPageScreen({ user, uid, onSave, onLogout, onDeleteAccount, onRegister, onLogin, email, setUser }) {

  const [show, setShow] = useState(false);
  const [editingProfile, setEditingProfile] = useState(() => {
    if (window.__openProfileEdit) { window.__openProfileEdit = false; return true; }
    return false;
  });
  const [showInquiry, setShowInquiry] = useState(false);
  const [inquiryText, setInquiryText] = useState('');
  const [inquirySending, setInquirySending] = useState(false);
  const [form, setForm] = useState({
    name: user.name || '',
    stage: user.stage || '',
    ivfPhase: user.ivfPhase || '',
    cycle: user.cycle ?? '',
    protocol: user.protocol || '',
    periodDate: user.periodDate || '',
    periodCycle: user.periodCycle || '',
    region1: user.region1 || '',
    region2: user.region2 || '',
    amh: user.amh || '',
    diagnoses: user.diagnoses || [],
    marriageStatus: user.marriageStatus || '',
    phone: user.phone || '',
    mode: user.mode || 'natural',
    hospital: user.hospital || '',
    nextAppointment: user.nextAppointment || '',
    nextAppointmentTime: user.nextAppointmentTime || '',
  });
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);
  const [showModeSwitch, setShowModeSwitch] = useState(false);
  const [notifSettings, setNotifSettings] = useState(user.notificationSettings || {});
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [phonePrompt, setPhonePrompt] = useState(false);
  const [phoneInput, setPhoneInput] = useState(user.phone || '');
  const [addingMedReminder, setAddingMedReminder] = useState(false);
  const [newMedName, setNewMedName] = useState('');
  const [newMedTime, setNewMedTime] = useState('08:00');
  useEffect(() => { setShow(true); }, []);

  useEffect(() => {
    setForm({
      name: user.name || '',
      stage: user.stage || '',
      ivfPhase: user.ivfPhase || '',
      cycle: user.cycle ?? '',
      protocol: user.protocol || '',
      periodDate: user.periodDate || '',
      periodCycle: user.periodCycle || '',
      region1: user.region1 || '',
      region2: user.region2 || '',
      amh: user.amh || '',
      diagnoses: user.diagnoses || [],
      marriageStatus: user.marriageStatus || '',
      phone: user.phone || '',
      mode: user.mode || 'natural',
      hospital: user.hospital || '',
      nextAppointment: user.nextAppointment || '',
      nextAppointmentTime: user.nextAppointmentTime || '',
    });
  }, [user]);

  const stageLabel = (() => {
    const labels = { consult: '상담/검사', timing: '타이밍법', iui: 'IUI', ivf: 'IVF' };
    return labels[user.stage] || user.stage || '';
  })();

  const handleToggleNotif = async (key, enabled) => {
    // 알림 켤 때 전화번호 없으면 입력 요청
    if (enabled && !form.phone) {
      setPhonePrompt(true);
      setPhoneInput('');
      return;
    }
    const updated = { ...notifSettings, [key]: { ...(notifSettings[key] || {}), enabled } };
    setNotifSettings(updated);
    if (setUser) setUser(prev => ({ ...prev, notificationSettings: updated }));
    try {
      await saveUserProfile(uid, { notification_settings: updated });
    } catch { /* silent */ }
  };

  const handlePhoneSubmit = async () => {
    if (phoneInput.length < 10) return;
    setForm(f => ({ ...f, phone: phoneInput }));
    if (setUser) setUser(prev => ({ ...prev, phone: phoneInput }));
    try {
      await saveUserProfile(uid, { phone: phoneInput });
    } catch { /* silent */ }
    setPhonePrompt(false);
    setToast('전화번호가 저장되었어요!');
    setTimeout(() => setToast(null), 2000);
  };

  const handleNotifTimeChange = async (key, time) => {
    const updated = { ...notifSettings, [key]: { ...(notifSettings[key] || {}), time } };
    setNotifSettings(updated);
    if (setUser) setUser(prev => ({ ...prev, notificationSettings: updated }));
    try {
      await saveUserProfile(uid, { notification_settings: updated });
    } catch { /* silent */ }
  };

  const handleProfileSave = async () => {
    setSaving(true);
    try {
      await onSave(form);
      setEditingProfile(false);
      setToast('저장되었어요!');
      setTimeout(() => setToast(null), 2000);
    } catch {
      setToast('저장에 실패했어요.');
      setTimeout(() => setToast(null), 2000);
    }
    setSaving(false);
  };

  const sectionStyle = {
    padding: '20px 24px', borderRadius: 14,
    border: `1px solid ${theme.border}`, background: theme.card,
    marginBottom: 12,
  };

  const fieldStyle = {
    marginBottom: 16,
  };
  const fieldLabel = {
    fontSize: 12, color: theme.textSub, marginBottom: 6,
  };
  const fieldValue = {
    fontSize: 15, fontWeight: 500, color: theme.text,
  };

  if (user?.isGuest) {
    return (
      <div className="page-content" style={{ flex: 1, overflow: 'auto', padding: '0 24px 40px' }}>
        <Header title="마이페이지" subtitle="내 정보 관리" />
        <div style={{ width: '100%' }}>
          <Fade show={show}>
            <div style={{
              background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 100%)`,
              borderRadius: 18, padding: '28px 32px', marginTop: 16, marginBottom: 20,
              color: '#fff', textAlign: 'center',
            }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🌱</div>
              <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>게스트로 체험 중이에요</div>
              <div style={{ fontSize: 14, opacity: 0.85, lineHeight: 1.6 }}>
                계정을 만들면 내 시술 단계에 맞는<br />맞춤형 케어를 받을 수 있어요
              </div>
            </div>
          </Fade>
          <Fade show={show} delay={100}>
            <button onClick={onRegister} style={{
              width: '100%', padding: '16px 0', borderRadius: 14,
              background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 100%)`,
              border: 'none', color: '#fff', fontSize: 16, fontWeight: 700,
              cursor: 'pointer', marginBottom: 12,
            }}>닉네임 등록하기</button>
          </Fade>
          <Fade show={show} delay={150}>
            <button onClick={onLogin} style={{
              width: '100%', padding: '14px 0', borderRadius: 14,
              background: '#fff', border: `1.5px solid ${theme.border}`,
              color: theme.text, fontSize: 14, fontWeight: 600,
              cursor: 'pointer',
            }}>기존 닉네임으로 로그인</button>
          </Fade>
        </div>
      </div>
    );
  }

  return (
    <div className="page-content" style={{ flex: 1, overflow: 'auto', padding: '0 24px 40px' }}>
      <Header title="마이페이지" subtitle="" />
      <div style={{ maxWidth: 960, margin: '0 auto', width: '100%' }}>

        {/* 프로필 카드 */}
        <Fade show={show}>
          <div style={{
            background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.accent} 100%)`,
            borderRadius: 18, padding: '24px 28px', marginTop: 12, marginBottom: 20,
            color: '#fff', display: 'flex', alignItems: 'center', gap: 16,
          }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14,
              background: 'rgba(255,255,255,0.2)', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              fontSize: 22, fontWeight: 700,
            }}>💉</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{user.name}</div>
              <div style={{ fontSize: 13, opacity: 0.8, marginTop: 3 }}>{stageLabel}</div>
            </div>
            <button onClick={() => setEditingProfile(true)} style={{
              background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: 10,
              padding: '8px 14px', color: '#fff', fontSize: 13, fontWeight: 600,
              cursor: 'pointer',
            }}>편집</button>
          </div>
        </Fade>

        {/* ── 프로필 편집 모달 ── */}
        {editingProfile && (
          <Fade show={show}>
            <div style={{ ...sectionStyle, padding: '24px 24px 16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: theme.text }}>프로필 편집</div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => setEditingProfile(false)} style={{ background: 'none', border: 'none', fontSize: 13, color: theme.textSub, cursor: 'pointer' }}>취소</button>
                  <button onClick={handleProfileSave} disabled={saving} style={{ background: 'none', border: 'none', fontSize: 13, color: theme.primary, fontWeight: 600, cursor: 'pointer' }}>
                    {saving ? '저장 중...' : '저장'}
                  </button>
                </div>
              </div>

              {/* 닉네임 */}
              <div style={fieldStyle}>
                <div style={fieldLabel}>닉네임</div>
                <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  style={{ ...inputStyle, fontSize: 15 }} />
              </div>

              {/* 시술 단계 + 회차 */}
                  <div style={fieldStyle}>
                    <div style={fieldLabel}>시술 단계</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {[
                        { v: 'consult', l: '상담/검사' },
                        { v: 'timing', l: '타이밍법' },
                        { v: 'iui', l: 'IUI' },
                        { v: 'ivf', l: 'IVF' },
                      ].map(s => (
                        <button key={s.v} onClick={() => setForm(f => ({ ...f, stage: s.v }))} style={{
                          padding: '9px 16px', borderRadius: 10,
                          border: `1.5px solid ${form.stage === s.v ? theme.primary : theme.border}`,
                          background: form.stage === s.v ? theme.primaryLight : 'transparent',
                          fontSize: 13, cursor: 'pointer', color: form.stage === s.v ? theme.primary : theme.text,
                        }}>{s.l}</button>
                      ))}
                    </div>
                  </div>
                  <div style={fieldStyle}>
                    <div style={fieldLabel}>회차</div>
                    <input value={form.cycle} onChange={e => setForm(f => ({ ...f, cycle: e.target.value }))}
                      placeholder="예: 1" style={{ ...inputStyle, maxWidth: 120 }} />
                  </div>

              {/* 생리 시작일 */}
              <div style={fieldStyle}>
                <div style={fieldLabel}>직전 생리 시작일</div>
                <input type="date" value={form.periodDate} onChange={e => setForm(f => ({ ...f, periodDate: e.target.value }))}
                  max={new Date().toISOString().split('T')[0]}
                  style={{ ...inputStyle, fontSize: 14 }} />
              </div>

              {/* 생리 주기 */}
              <div style={fieldStyle}>
                <div style={fieldLabel}>평균 생리 주기</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {[
                    { v: 'under21', l: '21일 이하' },
                    { v: '22to26', l: '22~26일' },
                    { v: '27to30', l: '27~30일' },
                    { v: 'over31', l: '31일 이상' },
                    { v: 'irregular', l: '불규칙' },
                  ].map(c => (
                    <button key={c.v} onClick={() => setForm(f => ({ ...f, periodCycle: c.v }))} style={{
                      padding: '8px 14px', borderRadius: 10,
                      border: `1.5px solid ${form.periodCycle === c.v ? theme.primary : theme.border}`,
                      background: form.periodCycle === c.v ? theme.primaryLight : 'transparent',
                      fontSize: 12, cursor: 'pointer', color: form.periodCycle === c.v ? theme.primary : theme.text,
                    }}>{c.l}</button>
                  ))}
                </div>
              </div>

              {/* 거주지 */}
              <div style={fieldStyle}>
                <div style={fieldLabel}>거주지</div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <select value={form.region1} onChange={e => setForm(f => ({ ...f, region1: e.target.value, region2: '' }))}
                    style={{ ...inputStyle, flex: 1, appearance: 'auto' }}>
                    <option value="">시/도</option>
                    {Object.keys(REGIONS).map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <select value={form.region2} onChange={e => setForm(f => ({ ...f, region2: e.target.value }))}
                    style={{ ...inputStyle, flex: 1, appearance: 'auto' }} disabled={!form.region1}>
                    <option value="">시/군/구</option>
                    {(REGIONS[form.region1] || []).map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
              </div>

              {/* 난임 진단명 + AMH */}
                  <div style={fieldStyle}>
                    <div style={fieldLabel}>난임 원인 진단명</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {DIAGNOSIS_OPTIONS.map(c => {
                        const checked = form.diagnoses.includes(c.id);
                        return (
                          <button key={c.id} onClick={() => {
                            setForm(f => {
                              if (c.id === 'unknown') return { ...f, diagnoses: checked ? [] : ['unknown'] };
                              const next = f.diagnoses.filter(x => x !== 'unknown');
                              return { ...f, diagnoses: next.includes(c.id) ? next.filter(x => x !== c.id) : [...next, c.id] };
                            });
                          }} style={{
                            padding: '8px 14px', borderRadius: 10,
                            border: `1.5px solid ${checked ? theme.primary : theme.border}`,
                            background: checked ? theme.primaryLight : 'transparent',
                            fontSize: 12, cursor: 'pointer', color: checked ? theme.primary : theme.text,
                          }}>{c.label}</button>
                        );
                      })}
                    </div>
                  </div>
                  <div style={fieldStyle}>
                    <div style={fieldLabel}>AMH 수치 (ng/mL)</div>
                    <input value={form.amh} onChange={e => setForm(f => ({ ...f, amh: e.target.value }))}
                      placeholder="예: 2.5" type="number" step="0.1"
                      style={{ ...inputStyle, maxWidth: 140 }} />
                  </div>

              {/* 혼인 상태 */}
              <div style={fieldStyle}>
                <div style={fieldLabel}>혼인 상태</div>
                <div style={{ display: 'flex', gap: 8 }}>
                  {[{ v: 'legal', l: '법적 혼인' }, { v: 'defacto', l: '사실혼' }, { v: '', l: '미입력' }].map(opt => (
                    <button key={opt.v} onClick={() => setForm(f => ({ ...f, marriageStatus: opt.v }))} style={{
                      padding: '9px 16px', borderRadius: 10,
                      border: `1.5px solid ${form.marriageStatus === opt.v ? theme.primary : theme.border}`,
                      background: form.marriageStatus === opt.v ? theme.primaryLight : 'transparent',
                      fontSize: 13, cursor: 'pointer', color: form.marriageStatus === opt.v ? theme.primary : theme.text,
                    }}>{opt.l}</button>
                  ))}
                </div>
              </div>

              {/* 전화번호 */}
              <div style={fieldStyle}>
                <div style={fieldLabel}>휴대전화번호</div>
                <input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value.replace(/[^0-9]/g, '') }))}
                  placeholder="01012345678" maxLength={11} inputMode="tel"
                  style={{ ...inputStyle, maxWidth: 200 }} />
              </div>

              {/* 병원 정보 */}
              <div style={fieldStyle}>
                <div style={fieldLabel}>다니는 병원</div>
                <input value={form.hospital} onChange={e => setForm(f => ({ ...f, hospital: e.target.value }))}
                  placeholder="예: 서울대학교병원 산부인과" style={{ ...inputStyle, fontSize: 14 }} />
              </div>

            </div>
          </Fade>
        )}

        {/* ── 저장한 글 ── */}
        <Fade show={show} delay={100}>
          <div style={sectionStyle}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 18 }}>📑</span>
              <div style={{ fontSize: 14, fontWeight: 600, color: theme.text }}>저장한 글</div>
            </div>
            <div style={{ fontSize: 13, color: theme.textSub, marginTop: 8 }}>준비중이에요</div>
          </div>
        </Fade>

        {/* ── 알림 설정 ── */}
        <Fade show={show} delay={200}>
          <div style={sectionStyle}>
            <div style={{ fontSize: 14, fontWeight: 600, color: theme.text, marginBottom: 16 }}>알림 설정</div>
            {/* 복용 리마인더 (여러 개 추가 가능) */}
            <div style={{ marginBottom: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500, color: theme.text }}>복용 리마인더</div>
                  <div style={{ fontSize: 12, color: theme.textSub, marginTop: 2 }}>약물/영양제 복용 시간에 알림</div>
                </div>
                <div onClick={() => {
                  if (!notifSettings.med_reminder_on && !form.phone) { setPhonePrompt(true); setPhoneInput(''); return; }
                  setNotifSettings(prev => ({ ...prev, med_reminder_on: !prev.med_reminder_on }));
                }} style={{
                  width: 44, height: 24, borderRadius: 12, cursor: 'pointer',
                  background: notifSettings.med_reminder_on ? theme.primary : theme.border,
                  position: 'relative', transition: 'background 0.2s',
                }}>
                  <div style={{
                    width: 20, height: 20, borderRadius: 10, background: '#fff',
                    position: 'absolute', top: 2, transition: 'left 0.2s',
                    left: notifSettings.med_reminder_on ? 22 : 2,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                  }} />
                </div>
              </div>
              {notifSettings.med_reminder_on && <>
              {/* 등록된 복용 리마인더 목록 */}
              {(notifSettings.med_reminders || []).map((rem, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 10, padding: '7px 0',
                  maxWidth: 460, paddingLeft: 8,
                }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: theme.primary, flexShrink: 0 }} />
                  <span style={{ fontSize: 14, width: 100, color: theme.text, flexShrink: 0 }}>{rem.name || '약물'}</span>
                  <select value={rem.time || '08:00'}
                    onChange={e => {
                      const updated = [...(notifSettings.med_reminders || [])];
                      updated[i] = { ...updated[i], time: e.target.value, _dirty: true };
                      setNotifSettings(prev => ({ ...prev, med_reminders: updated }));
                    }}
                    style={{ ...inputStyle, width: 130, fontSize: 13, padding: '6px 10px', flexShrink: 0 }}>
                    {Array.from({ length: 48 }, (_, i) => { const h = String(Math.floor(i/2)).padStart(2,'0'); const m = i%2===0?'00':'30'; return <option key={`${h}:${m}`} value={`${h}:${m}`}>{`${h}:${m}`}</option>; })}
                  </select>
                  {rem._dirty && <button onClick={() => {
                    const cleaned = (notifSettings.med_reminders || []).map(r => { const { _dirty, ...rest } = r; return rest; });
                    const newSettings = { ...notifSettings, med_reminders: cleaned };
                    setNotifSettings(newSettings);
                    saveUserProfile(uid, { notification_settings: newSettings }).catch(() => {});
                  }} style={{
                    background: theme.primary, border: 'none', borderRadius: 8,
                    padding: '5px 12px', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}>저장</button>}
                  <button onClick={() => {
                    const updated = (notifSettings.med_reminders || []).filter((_, j) => j !== i);
                    const newSettings = { ...notifSettings, med_reminders: updated };
                    setNotifSettings(newSettings);
                    saveUserProfile(uid, { notification_settings: newSettings }).catch(() => {});
                  }} style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: theme.textSub, fontSize: 13,
                  }}
                  onMouseEnter={e => e.target.style.color = '#e74c3c'}
                  onMouseLeave={e => e.target.style.color = theme.textSub}
                  >🗑️</button>
                </div>
              ))}
              {/* 추가 폼 */}
              {addingMedReminder ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10, maxWidth: 460 }}>
                  <input value={newMedName} onChange={e => setNewMedName(e.target.value)}
                    placeholder="약물/영양제 이름"
                    style={{ ...inputStyle, fontSize: 13, padding: '8px 12px', width: 160 }} autoFocus />
                  <select value={newMedTime} onChange={e => setNewMedTime(e.target.value)}
                    style={{ ...inputStyle, width: 110, fontSize: 13, padding: '8px 10px' }}>
                    {Array.from({ length: 48 }, (_, i) => { const h = String(Math.floor(i/2)).padStart(2,'0'); const m = i%2===0?'00':'30'; return <option key={`${h}:${m}`} value={`${h}:${m}`}>{`${h}:${m}`}</option>; })}
                  </select>
                  <button onClick={() => {
                    if (!newMedName.trim()) return;
                    const updated = [...(notifSettings.med_reminders || []), { name: newMedName.trim(), time: newMedTime }];
                    const newSettings = { ...notifSettings, med_reminders: updated };
                    setNotifSettings(newSettings);
                    saveUserProfile(uid, { notification_settings: newSettings }).catch(() => {});
                    setNewMedName(''); setNewMedTime('08:00'); setAddingMedReminder(false);
                  }} style={{
                    background: theme.primary, border: 'none', borderRadius: 8,
                    padding: '8px 16px', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
                  }}>저장</button>
                  <button onClick={() => { setAddingMedReminder(false); setNewMedName(''); setNewMedTime('08:00'); }} style={{
                    background: 'none', border: `1px solid ${theme.border}`, borderRadius: 8,
                    padding: '8px 12px', color: theme.textSub, fontSize: 13, cursor: 'pointer',
                  }}>취소</button>
                </div>
              ) : (
                <button onClick={() => setAddingMedReminder(true)} style={{
                  marginTop: 8, fontSize: 13, color: theme.primary,
                  background: 'none', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 4, padding: 0,
                }}>
                  <span style={{ fontSize: 15 }}>+</span> 복용 리마인더 추가
                </button>
              )}
              </>}
            </div>

            {/* 나머지 알림 */}
            {[
              { key: 'timeline_health_check', label: '메디컬 체크', desc: '타임라인별 맞춤 메디컬 알림' },
            ].map((item, idx, arr) => {
              const setting = notifSettings[item.key] || {};
              const enabled = !!setting.enabled;
              return (
                <div key={item.key} style={{ marginBottom: idx < arr.length - 1 ? 18 : 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 500, color: theme.text }}>{item.label}</div>
                      <div style={{ fontSize: 12, color: theme.textSub, marginTop: 2 }}>{item.desc}</div>
                    </div>
                    <button onClick={() => handleToggleNotif(item.key, !enabled)} style={{
                      width: 46, height: 26, borderRadius: 13, border: 'none', cursor: 'pointer',
                      background: enabled ? theme.primary : theme.border,
                      position: 'relative', flexShrink: 0, transition: 'background 0.2s',
                    }}>
                      <div style={{
                        width: 20, height: 20, borderRadius: 10, background: '#fff',
                        position: 'absolute', top: 3, left: enabled ? 23 : 3, transition: 'left 0.2s',
                      }} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </Fade>

        {/* 전화번호 입력 팝업 */}
        {phonePrompt && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.4)', zIndex: 200,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }} onClick={() => setPhonePrompt(false)}>
            <div style={{
              background: '#fff', borderRadius: 16, padding: 28, width: '85%', maxWidth: 360,
            }} onClick={e => e.stopPropagation()}>
              <div style={{ fontSize: 16, fontWeight: 700, color: theme.text, marginBottom: 8 }}>전화번호 입력</div>
              <div style={{ fontSize: 13, color: theme.textSub, marginBottom: 16 }}>알림톡을 받을 전화번호를 입력해주세요.</div>
              <input value={phoneInput} onChange={e => setPhoneInput(e.target.value.replace(/[^0-9]/g, ''))}
                placeholder="01012345678" maxLength={11} inputMode="tel"
                style={{ ...inputStyle, fontSize: 16, textAlign: 'center', letterSpacing: 2, marginBottom: 16 }} />
              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={() => setPhonePrompt(false)} style={{
                  flex: 1, padding: '12px', borderRadius: 10, border: `1.5px solid ${theme.border}`,
                  background: '#fff', fontSize: 14, fontWeight: 600, color: theme.textSub, cursor: 'pointer',
                }}>취소</button>
                <button onClick={handlePhoneSubmit} disabled={phoneInput.length < 10} style={{
                  ...btnPrimary, flex: 1, opacity: phoneInput.length < 10 ? 0.4 : 1,
                }}>확인</button>
              </div>
            </div>
          </div>
        )}

        {/* ── 일반 설정 ── */}
        <Fade show={show} delay={300}>
          <div style={sectionStyle}>
            <div style={{ fontSize: 14, fontWeight: 600, color: theme.text, marginBottom: 12 }}>일반</div>
            <div style={{
              padding: '12px 0', borderBottom: `1px solid ${theme.border}`,
              fontSize: 14, color: theme.text, cursor: 'default',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span>파트너 연동하기</span>
              <span style={{ fontSize: 12, color: theme.textSub, background: theme.primaryBg, padding: '2px 8px', borderRadius: 8 }}>준비중</span>
            </div>
            <div onClick={() => setShowPrivacy(true)} style={{
              padding: '12px 0', borderBottom: `1px solid ${theme.border}`,
              fontSize: 14, color: theme.text, cursor: 'pointer',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span>개인정보처리방침</span>
              <span style={{ color: theme.textSub, fontSize: 14 }}>›</span>
            </div>
            <div onClick={() => setShowInquiry(true)} style={{
              padding: '12px 0',
              fontSize: 14, color: theme.text, cursor: 'pointer',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span>문의 및 피드백</span>
              <span style={{ color: theme.textSub, fontSize: 14 }}>›</span>
            </div>
            <div onClick={() => setShowModeSwitch(true)} style={{
              padding: '12px 0', borderTop: `1px solid ${theme.border}`,
              fontSize: 14, color: theme.primary, cursor: 'pointer',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span>기본 모드로 전환</span>
              <span style={{ color: theme.textSub, fontSize: 14 }}>›</span>
            </div>
          </div>
        </Fade>

        {/* 로그아웃 */}
        <Fade show={show} delay={400}>
          <button onClick={onLogout} style={{
            width: '100%', padding: '14px 0', borderRadius: 12,
            border: `1px solid ${theme.border}`, background: theme.card,
            fontSize: 14, color: '#C44', cursor: 'pointer', marginTop: 8,
          }}>로그아웃</button>
        </Fade>

        {/* 탈퇴 */}
        <Fade show={show} delay={440}>
          <button onClick={async () => {
            if (!window.confirm('정말 탈퇴하시겠어요?\n모든 데이터가 삭제되며 복구할 수 없습니다.')) return;
            try { await onDeleteAccount(); } catch { }
          }} style={{
            width: '100%', padding: '12px 0', borderRadius: 12,
            border: 'none', background: 'transparent',
            fontSize: 13, color: theme.textSub, cursor: 'pointer', marginTop: 4,
            textDecoration: 'underline',
          }}>회원 탈퇴</button>
        </Fade>

        {/* 모드 전환 모달 */}
        {showModeSwitch && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.45)', zIndex: 200,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }} onClick={() => setShowModeSwitch(false)}>
            <div onClick={e => e.stopPropagation()} style={{
              background: '#fff', borderRadius: 24, padding: '36px 32px 28px', maxWidth: 400, width: '90%',
              textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
            }}>
              <div style={{ width: 56, height: 56, borderRadius: 16, background: '#F2EFFA', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', fontSize: 24 }}>🌸</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#2A2440', marginBottom: 10 }}>기본 모드로 전환할까요?</div>
              <div style={{ fontSize: 14, color: '#8C839E', lineHeight: 1.6, marginBottom: 20 }}>배란일 예측과 주기 기록 중심의<br/>기본 모드로 전환돼요.</div>
              <div style={{ background: '#F6F4FB', borderRadius: 14, padding: '16px 20px', textAlign: 'left', marginBottom: 24 }}>
                {['생리 주기 기반으로 관리돼요', '기존 시술 데이터는 보관돼요', '언제든 다시 전환할 수 있어요'].map((t, i) => (
                  <div key={i} style={{ fontSize: 14, color: '#2A2440', lineHeight: 1.8, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: theme.primary, flexShrink: 0 }} />{t}
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 12 }}>
                <button onClick={() => setShowModeSwitch(false)} style={{
                  flex: 1, padding: '14px', borderRadius: 14, border: '1.5px solid #E8E4F0', background: '#fff',
                  fontSize: 15, fontWeight: 600, color: '#6B5F82', cursor: 'pointer',
                }}>취소</button>
                <button onClick={async () => {
                  setShowModeSwitch(false);
                  try { await saveUserProfile(uid, { mode: 'natural' }); setUser(prev => ({ ...prev, mode: 'natural' })); window.location.reload(); } catch {}
                }} style={{
                  flex: 1, padding: '14px', borderRadius: 14, border: 'none',
                  background: `linear-gradient(135deg, ${theme.primary}, #9B8CD9)`, color: '#fff',
                  fontSize: 15, fontWeight: 600, cursor: 'pointer',
                }}>전환하기</button>
              </div>
            </div>
          </div>
        )}

        {/* 문의 모달 */}
        {showInquiry && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.45)', zIndex: 200,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }} onClick={() => { setShowInquiry(false); setInquiryText(''); }}>
            <div onClick={e => e.stopPropagation()} style={{
              background: '#fff', borderRadius: 20, padding: '28px 24px', maxWidth: 440, width: '90%',
              boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
            }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#2A2440', marginBottom: 6 }}>문의하기</div>
              <div style={{ fontSize: 13, color: '#8C839E', marginBottom: 16 }}>궁금한 점이나 불편사항을 알려주세요</div>
              <textarea value={inquiryText} onChange={e => setInquiryText(e.target.value)} placeholder="내용을 입력해주세요" rows={5} style={{ width: '100%', padding: '14px', borderRadius: 12, border: `1.5px solid ${theme.border}`, fontSize: 14, fontFamily: 'inherit', resize: 'vertical', outline: 'none', boxSizing: 'border-box' }} />
              <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
                <button onClick={() => { setShowInquiry(false); setInquiryText(''); }} style={{ flex: 1, padding: '12px', borderRadius: 12, border: `1.5px solid ${theme.border}`, background: '#fff', fontSize: 14, fontWeight: 600, color: '#6B5F82', cursor: 'pointer' }}>취소</button>
                <button disabled={!inquiryText.trim() || inquirySending} onClick={async () => { setInquirySending(true); try { const { getFirestore, collection, addDoc, serverTimestamp } = await import('firebase/firestore'); const db = getFirestore(); await addDoc(collection(db, 'inquiries'), { uid, nickname: user.name, mode: user.mode || '', message: inquiryText.trim(), createdAt: serverTimestamp(), status: 'pending' }); alert('문의가 접수되었어요!'); setShowInquiry(false); setInquiryText(''); } catch(e) { alert('전송 실패'); } setInquirySending(false); }} style={{ flex: 1, padding: '12px', borderRadius: 12, border: 'none', background: inquiryText.trim() ? theme.primary : '#D1D1D6', color: '#fff', fontSize: 14, fontWeight: 600, cursor: inquiryText.trim() ? 'pointer' : 'default', opacity: inquirySending ? 0.6 : 1 }}>{inquirySending ? '전송 중...' : '보내기'}</button>
              </div>
            </div>
          </div>
        )}

        {/* 개인정보처리방침 모달 */}
        {showPrivacy && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.5)', zIndex: 200,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }} onClick={() => setShowPrivacy(false)}>
            <div style={{
              background: '#fff', borderRadius: 16, padding: '24px 20px',
              width: '90%', maxWidth: 500, maxHeight: '80vh', overflow: 'auto',
            }} onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <span style={{ fontSize: 16, fontWeight: 700 }}>개인정보처리방침</span>
                <button onClick={() => setShowPrivacy(false)} style={{ background: 'none', border: 'none', fontSize: 20, color: theme.textSub, cursor: 'pointer' }}>×</button>
              </div>
              <div style={{ fontSize: 13, color: theme.text, lineHeight: 1.9, whiteSpace: 'pre-line' }}>
                {PRIVACY_POLICY_TEXT}
              </div>
            </div>
          </div>
        )}

        {/* 토스트 */}
        {toast && (
          <div style={{
            position: 'fixed', bottom: 40, left: '50%', transform: 'translateX(-50%)',
            padding: '12px 28px', borderRadius: 12, background: theme.text,
            color: '#fff', fontSize: 14, fontWeight: 600,
            boxShadow: '0 8px 30px rgba(0,0,0,0.2)', zIndex: 100,
          }}>{toast}</div>
        )}
      </div>
    </div>
  );
}
