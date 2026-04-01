import { useState, useMemo } from 'react';
import { theme, inputStyle, btnPrimary } from '../styles/theme';
import { Fade } from '../components/Layout';

// 동의서 전문 내용
const CONSENT_TEXTS = {
  privacy: `라일(Lyle)은 서비스 제공을 위해 아래와 같이 개인정보를 수집·이용합니다.

1. 수집 항목
  - 닉네임, 생년월일, 거주지(시/도 단위), 기혼 여부
  - 휴대전화번호 (알림 서비스 신청 시)

2. 수집·이용 목적
  - 이용자 맞춤형 난임 치료 정보 및 콘텐츠 제공
  - 알림 서비스 제공 (카카오톡 알림톡)
  - 서비스 개선을 위한 이용 통계 분석

3. 보유 기간: 회원 탈퇴 시 즉시 파기

이용자는 동의를 거부할 권리가 있으나, 필수 항목에 대한 동의를 거부할 경우 서비스 이용이 제한됩니다.`,

  sensitive: `라일(Lyle)은 맞춤형 서비스 제공을 위해 「개인정보 보호법」 제23조에 따른 민감정보를 아래와 같이 수집·이용합니다.

1. 수집 항목
  - 건강 및 의료 관련 정보 (난임 진단명, 시술 단계 및 회차, 생리 시작일, 생리 주기, 복용 중인 약물·영양제, 기타 이용자가 대화 중 직접 제공한 건강 관련 정보 등)

2. 수집·이용 목적
  - 이용자 맞춤형 난임 치료 정보 제공

3. 보유 기간: 회원 탈퇴 시 즉시 파기

대화 중 수집·저장된 건강 및 의료 관련 정보는 '기록됨' 카드를 통해 저장 사실을 즉시 안내하며, '채팅 기억' 메뉴에서 이용자가 직접 열람하고 삭제할 수 있습니다.

이용자는 민감정보 수집에 동의하지 않을 수 있으나, 동의하지 않을 경우 맞춤형 서비스 기능의 일부가 제한될 수 있습니다.`,

  notification: `라일(Lyle)은 카카오톡 알림톡을 통해 이용자의 치료 여정에 맞춘 복약 알림 및 메디컬 체크 알림을 발송합니다.

1. 수집 항목: 휴대전화번호

2. 이용 목적: 복약 리마인더, 메디컬 체크 알림 발송

3. 보유 기간: 알림 서비스 해지 시 즉시 파기

알림톡 발송은 카카오 공식 딜러사(알리고)를 통해 처리되며, 발송 목적으로만 휴대전화번호가 제공됩니다.

알림 서비스는 선택 사항이며, 동의하지 않아도 서비스 이용에 제한이 없습니다. 동의 후에도 서비스 내 설정에서 언제든지 수신을 거부하거나 해지할 수 있습니다.`,
};

// ── Mode options ──
const MODE_OPTIONS = [
  {
    id: 'natural',
    emoji: '\uD83C\uDF38',
    label: '자연임신 준비',
    desc: '배란일 체크, 주기 기록, 생활 관리',
  },
  {
    id: 'medical',
    emoji: '\uD83D\uDC89',
    label: '병원 시술 중심 관리',
    desc: '타이밍법·인공수정·시험관 일정, 주사·약 관리',
  },
];

// ── Cycle length options ──
const CYCLE_OPTIONS = [
  { value: 'under21', label: '21일 이하' },
  { value: '22to26', label: '22~26일' },
  { value: '27to30', label: '27~30일 (평균)' },
  { value: 'over31', label: '31일 이상' },
  { value: 'irregular', label: '불규칙' },
];

// ── Procedure options ──
const PROCEDURE_OPTIONS = [
  { id: 'consult', label: '상담 및 검사 중이에요', desc: '아직 시술 방향 미정' },
  { id: 'timing', label: '타이밍법', desc: '배란 유도와 함께 자연 임신 시도' },
  { id: 'iui', label: '인공수정 (IUI)', desc: '배란 유도와 함께 정자 주입 시술' },
  { id: 'ivf', label: '체외수정 (IVF)', desc: '시험관 아기 시술' },
];

// ── IUI sub-stages ──
const IUI_STAGE_OPTIONS = [
  { value: 'preparing', label: '시술 준비 중', desc: '배란 유도 주사·약 복용 중' },
  { value: 'waiting', label: '시술 후 대기', desc: 'IUI 시술 완료, 결과 대기 중' },
];

// ── IVF protocol options ──
const IVF_PROTOCOL_OPTIONS = [
  { value: 'long', label: '장기요법 (Long protocol)' },
  { value: 'short', label: '단기요법 (Short protocol)' },
  { value: 'antagonist', label: '길항제요법 (Antagonist)' },
  { value: 'natural', label: '자연주기 (Natural cycle)' },
  { value: 'unknown', label: '잘 모르겠어요' },
];

// ── IVF sub-stages ──
const IVF_STAGE_OPTIONS = [
  { value: 'retrieval_prep', label: '채취 준비 중', desc: '과배란 주사·모니터링 진행 중' },
  { value: 'fresh_wait', label: '신선배아이식 후 대기', desc: '이식 완료, 착상 결과 대기 중' },
  { value: 'frozen_prep', label: '동결 후 이식 준비 중', desc: '배아 동결 완료, FET 이식 준비' },
  { value: 'frozen_wait', label: '동결배아이식 후 대기', desc: 'FET 이식 완료, 착상 결과 대기 중' },
];

// ── Done screen messages ──
function getDoneMessage(form) {
  if (form.mode === 'natural') {
    return {
      emoji: '\uD83C\uDF38',
      title: '자연임신 준비, 라일이 함께할게요',
      sub: '배란일 예측과 주기 기록으로\n건강한 임신 준비를 도와드릴게요.',
    };
  }
  if (form.procedure === 'consult') {
    return {
      emoji: '\uD83D\uDC89',
      title: '상담·검사 단계, 함께 준비해요',
      sub: '필요한 검사와 일정을\n라일이 꼼꼼히 챙겨드릴게요.',
    };
  }
  if (form.procedure === 'timing') {
    return {
      emoji: '\uD83D\uDC89',
      title: '타이밍법, 라일이 함께할게요',
      sub: '배란 시기에 맞춘 일정 관리와\n생활 습관을 안내해드릴게요.',
    };
  }
  if (form.procedure === 'iui') {
    return {
      emoji: '\uD83D\uDC89',
      title: '인공수정(IUI), 함께 준비해요',
      sub: '시술 일정과 주의사항을\n라일이 꼼꼼히 안내해드릴게요.',
    };
  }
  if (form.procedure === 'ivf') {
    return {
      emoji: '\uD83D\uDC89',
      title: '체외수정(IVF), 함께 준비해요',
      sub: '복잡한 시술 과정도\n라일이 하나하나 함께할게요.',
    };
  }
  return {
    emoji: '\uD83C\uDF31',
    title: '라일이 함께할게요',
    sub: '당신의 여정을 응원합니다.',
  };
}

// ── Progress bar component ──
function ProgressBar({ current, total }) {
  const pct = Math.round((current / total) * 100);
  return (
    <div style={{ width: '100%', height: 4, background: theme.border, borderRadius: 2 }}>
      <div style={{
        width: `${pct}%`,
        height: '100%',
        background: `linear-gradient(90deg, ${theme.primary}, ${theme.accent})`,
        borderRadius: 2,
        transition: 'width 0.4s ease',
      }} />
    </div>
  );
}

// ── Radio card component ──
function RadioCard({ selected, emoji, label, desc, onClick, delay = 0, show = true }) {
  return (
    <Fade show={show} delay={delay}>
      <button onClick={onClick} style={{
        display: 'flex', alignItems: 'center', gap: 14,
        padding: '16px 20px', borderRadius: theme.radius,
        border: `1.5px solid ${selected ? theme.primary : theme.border}`,
        background: selected ? theme.primaryLight : theme.card,
        cursor: 'pointer', width: '100%', textAlign: 'left',
        transition: 'all 0.2s',
      }}>
        {emoji && <span style={{ fontSize: 28, flexShrink: 0 }}>{emoji}</span>}
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: theme.text }}>{label}</div>
          {desc && <div style={{ fontSize: 12, color: theme.textSub, marginTop: 3, lineHeight: 1.5 }}>{desc}</div>}
        </div>
        {selected && <span style={{ color: theme.primary, fontSize: 18, fontWeight: 700 }}>✓</span>}
      </button>
    </Fade>
  );
}

// ── Step wrapper ──
function StepLayout({ tag, question, subtitle, children, show, onBack, onSkip, progress, totalSteps }) {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      {/* Top bar: progress + skip */}
      <div style={{
        padding: '16px 24px 0',
        position: 'sticky', top: 0, zIndex: 5,
        background: theme.bg,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ fontSize: 12, color: theme.textSub }}>{progress} / {totalSteps}</div>
          {onSkip && (
            <button onClick={onSkip} style={{
              background: 'none', border: 'none', fontSize: 13,
              color: theme.textSub, cursor: 'pointer', padding: '4px 0',
            }}>건너뛰기</button>
          )}
        </div>
        <ProgressBar current={progress} total={totalSteps} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: '0 24px 24px', maxWidth: 540, width: '100%', margin: '0 auto', boxSizing: 'border-box' }}>
        <Fade show={show}>
          <div style={{ marginTop: 32, marginBottom: 28 }}>
            {tag && (
              <span style={{
                display: 'inline-block', padding: '4px 12px', borderRadius: 20,
                background: theme.primaryLight, color: theme.primary,
                fontSize: 12, fontWeight: 600, marginBottom: 12,
              }}>{tag}</span>
            )}
            <h2 style={{
              fontSize: 22, fontWeight: 700, color: theme.text,
              lineHeight: 1.4, margin: 0, letterSpacing: -0.3,
            }}>{question}</h2>
            {subtitle && (
              <p style={{ fontSize: 14, color: theme.textSub, margin: '8px 0 0', lineHeight: 1.6 }}>{subtitle}</p>
            )}
          </div>
          {children}
        </Fade>

        {/* Back button */}
        {onBack && (
          <button onClick={onBack} style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'none', border: 'none',
            fontSize: 14, color: theme.textSub, cursor: 'pointer',
            padding: '16px 0 8px', margin: '0 auto',
          }}>
            <span style={{ fontSize: 16 }}>←</span> 이전으로
          </button>
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════
// Main component
// ════════════════════════════════════════
export default function OnboardingScreen({ onComplete, defaultName = '', onCancel, onGuest, onLogin }) {
  const [step, setStep] = useState(0);
  const [show, setShow] = useState(true);
  const [direction, setDirection] = useState(1); // 1 = forward, -1 = back
  const [consent, setConsent] = useState({ privacy: false, sensitive: false, notification: false });
  const [expandedConsent, setExpandedConsent] = useState(null);

  const [form, setForm] = useState({
    mode: '',           // 'natural' | 'medical'
    periodDate: '',     // YYYY-MM-DD
    cycle: '',          // cycle length category
    procedure: '',      // 'consult' | 'timing' | 'iui' | 'ivf'
    protocol: '',       // IVF protocol
    stage: '',          // IUI stage or IVF stage
    phone: '',          // if notification consent
    nickname: defaultName || '',  // 닉네임
  });

  const update = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const goTo = (target) => {
    setDirection(target > step ? 1 : -1);
    setShow(false);
    setTimeout(() => {
      setStep(target);
      setShow(true);
    }, 280);
  };

  const goNext = () => goTo(step + 1);
  const goBack = () => goTo(step - 1);

  // ── Compute total steps and step mapping ──
  // Step 0: consent
  // Step 1: mode selection
  // Step 2: period date
  // Step 3: depends on mode
  //   natural: cycle → done
  //   medical: procedure selection
  // Step 4: depends on procedure
  //   consult → done (no step 4)
  //   timing → cycle → done
  //   iui → IUI stage → done
  //   ivf → protocol
  // Step 5: IVF only → IVF stage → done
  // Step 6: phone (if notification consent) → done
  // Final: done screen

  const totalSteps = useMemo(() => {
    // mode(1) + consent(2) + period(3) + ...
    let count = 4; // mode + consent + period + cycle/procedure
    if (form.mode === 'natural') {
      count = 4; // mode + consent + period + cycle
    } else if (form.mode === 'medical') {
      if (form.procedure === 'consult') count = 4; // mode + consent + period + procedure
      else if (form.procedure === 'timing') count = 5; // + cycle
      else if (form.procedure === 'iui') count = 5; // + iui stage
      else if (form.procedure === 'ivf') count = 6; // + protocol + ivf stage
      else count = 4;
    }
    if (consent.notification) count += 1; // phone step
    return count;
  }, [form.mode, form.procedure, consent.notification]);

  // Map logical step number to progress number (1-based, excluding consent)
  const progressNum = step > 0 ? step : 0;

  const canConsent = consent.privacy && consent.sensitive;
  const allConsent = consent.privacy && consent.sensitive && consent.notification;
  const toggleAll = () => {
    const next = !allConsent;
    setConsent({ privacy: next, sensitive: next, notification: next });
  };

  const disabledBtn = { ...btnPrimary, opacity: 0.4, cursor: 'not-allowed' };

  // ── Determine what step numbers map to ──
  // This is a dynamic step flow, so we compute the "logical" steps on the fly
  // step 0: mode (필수, 건너뛰기 불가)
  // step 1: consent (게스트로 이용하기 가능)
  // step 2: period
  // step 3+: branching

  // Helper: get the next step from current step with auto-advance logic
  const getStepAfter = (currentStep) => currentStep + 1;

  // Helper: figure out what the "done" step number is
  const getDoneStep = () => {
    let s = 3; // after mode(1) + period(2)
    if (form.mode === 'natural') {
      s = 4; // after cycle(3)
    } else {
      // medical: after procedure(3)
      if (form.procedure === 'consult') {
        s = 4;
      } else if (form.procedure === 'timing') {
        s = 5; // after cycle(4)
      } else if (form.procedure === 'iui') {
        s = 5; // after iui stage(4)
      } else if (form.procedure === 'ivf') {
        s = 6; // after protocol(4) + ivf stage(5)
      } else {
        s = 4;
      }
    }
    if (consent.notification) s += 1; // phone step before done
    return s;
  };

  const doneStep = getDoneStep();

  // Check if current step is the phone step (the step right before done, only if notification consent)
  const phoneStep = consent.notification ? doneStep - 1 : -1;
  // If phone step exists, it comes just before done, shifting done up by 1
  // Actually let's track: the phone step is always the one just before done

  const handleComplete = () => {
    onComplete({
      ...form,
      consent,
    });
  };

  // ══════════════════════════════
  // STEP 0: Mode selection (필수)
  // ══════════════════════════════
  if (step === 0) return (
    <StepLayout
      tag="준비 방법"
      question="lyle과 함께&#10;어떤 준비를 하고 싶으세요?"
      subtitle="선택에 맞게 홈 화면과 알림을 세팅해 드릴게요"
      show={show}
      progress={1}
      totalSteps={totalSteps}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {MODE_OPTIONS.map((m, i) => (
          <RadioCard
            key={m.id}
            selected={form.mode === m.id}
            emoji={m.emoji}
            label={m.label}
            desc={m.desc}
            show={show}
            delay={i * 80}
            onClick={() => {
              update('mode', m.id);
              if (m.id === 'natural') {
                update('procedure', '');
                update('protocol', '');
                update('stage', '');
              }
            }}
          />
        ))}
      </div>

      <button
        onClick={goNext}
        disabled={!form.mode}
        style={form.mode ? { ...btnPrimary, marginTop: 32 } : { ...disabledBtn, marginTop: 32 }}
      >
        다음
      </button>

      {onLogin && (
        <button onClick={onLogin} style={{
          width: '100%', padding: '12px 0', marginTop: 12,
          border: 'none', background: 'transparent',
          fontSize: 13, color: theme.textSub, cursor: 'pointer',
        }}>
          이미 등록하셨나요? <span style={{ fontWeight: 600, color: theme.primary, textDecoration: 'underline' }}>로그인</span>
        </button>
      )}
    </StepLayout>
  );

  // ══════════════════════════════
  // STEP 1: Consent
  // ══════════════════════════════
  if (step === 1) return (
    <div style={{ flex: 1, padding: '0 24px 24px', overflow: 'auto' }}>
      {/* 프로그레스 바 + 건너뛰기 */}
      <div style={{ padding: '12px 0 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: theme.textSub }}>{step + 1} / {totalSteps}</span>
        {onGuest && <button onClick={() => onGuest(form.mode)} style={{ background: 'none', border: 'none', fontSize: 13, color: theme.textSub, cursor: 'pointer' }}>건너뛰기</button>}
      </div>
      <div style={{ height: 3, background: theme.border, borderRadius: 2, margin: '6px 0 8px' }}>
        <div style={{ height: '100%', width: `${((step + 1) / totalSteps) * 100}%`, background: theme.primary, borderRadius: 2 }} />
      </div>
      <div style={{
        padding: '16px 0 10px',
        display: 'flex', alignItems: 'center', gap: 12,
      }}>
        <button onClick={() => goTo(0)} style={{
          background: 'none', border: 'none', fontSize: 20,
          cursor: 'pointer', color: theme.primary, padding: 4, lineHeight: 1,
        }}>←</button>
        <div style={{ fontSize: 18, fontWeight: 700, color: theme.text }}>서비스 이용 동의</div>
      </div>
      <Fade show={show}>
        <div style={{ maxWidth: 500, margin: '0 auto' }}>
          <p style={{ fontSize: 14, color: theme.textSub, margin: '12px 0 24px', lineHeight: 1.6 }}>
            라일 서비스 이용을 위해 아래 약관에 동의해주세요.
          </p>

          {/* 전체 동의 */}
          <label style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '16px 18px', borderRadius: theme.radius,
            border: `1.5px solid ${allConsent ? theme.primary : theme.border}`,
            background: allConsent ? theme.primaryLight : theme.card,
            cursor: 'pointer', marginBottom: 16,
          }}>
            <input type="checkbox" checked={allConsent} onChange={toggleAll}
              style={{ accentColor: theme.primary, width: 20, height: 20 }} />
            <span style={{ fontSize: 15, fontWeight: 600, color: theme.text }}>전체 동의</span>
          </label>

          <div style={{ borderTop: `1px solid ${theme.border}`, paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { key: 'privacy', label: '[필수] 개인정보 수집·이용 동의', required: true },
              { key: 'sensitive', label: '[필수] 민감정보(건강·의료 정보) 수집·이용 동의', required: true },
              { key: 'notification', label: '[선택] 메디컬 체크 및 복약 알림톡 수신 동의', required: false },
            ].map(item => (
              <div key={item.key}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', flex: 1 }}>
                    <input type="checkbox" checked={consent[item.key]}
                      onChange={() => setConsent(c => ({ ...c, [item.key]: !c[item.key] }))}
                      style={{ accentColor: theme.primary, width: 18, height: 18 }} />
                    <span style={{ fontSize: 13, color: theme.text }}>{item.label}</span>
                  </label>
                  <span onClick={() => setExpandedConsent(expandedConsent === item.key ? null : item.key)}
                    style={{ fontSize: 12, color: theme.primary, cursor: 'pointer', whiteSpace: 'nowrap' }}>
                    {expandedConsent === item.key ? '닫기' : '전문 보기'}
                  </span>
                </div>
                {expandedConsent === item.key && (
                  <div style={{
                    marginTop: 8, padding: 16, borderRadius: 12,
                    background: theme.primaryBg, border: `1px solid ${theme.primaryLight}`,
                    fontSize: 12, color: theme.textSub, lineHeight: 1.8, whiteSpace: 'pre-line',
                  }}>
                    {CONSENT_TEXTS[item.key]}
                  </div>
                )}
              </div>
            ))}
          </div>

          <button onClick={goNext} disabled={!canConsent}
            style={canConsent ? { ...btnPrimary, marginTop: 32 } : { ...disabledBtn, marginTop: 32 }}>
            동의하고 시작하기
          </button>

        </div>
      </Fade>
    </div>
  );

  // ══════════════════════════════
  // STEP 2: Period date
  // ══════════════════════════════
  if (step === 2) return (
    <StepLayout
      tag="생리 정보"
      question="마지막 생리 시작일이 언제인가요?"
      subtitle="정확한 날짜를 몰라도 괜찮아요. 대략적으로 입력해주세요."
      show={show}
      onBack={() => goTo(1)}
      onSkip={() => onGuest && onGuest(form.mode)}
      progress={3}
      totalSteps={totalSteps}
    >
      <div style={{
        padding: 20, borderRadius: 16, background: theme.primaryBg,
        border: `1px solid ${theme.primaryLight}`, marginBottom: 24,
      }}>
        <input
          type="date"
          value={form.periodDate}
          onChange={e => update('periodDate', e.target.value)}
          max={new Date().toISOString().split('T')[0]}
          style={{
            ...inputStyle,
            background: '#fff',
            fontSize: 16,
            padding: '14px 16px',
            width: '100%',
            boxSizing: 'border-box',
          }}
        />
      </div>

      <div style={{
        padding: '14px 16px', borderRadius: 12, background: '#FFFBF0',
        border: '1px solid #F0E6CC', marginBottom: 24,
      }}>
        <div style={{ fontSize: 12, color: '#9E8B5E', lineHeight: 1.6 }}>
          이 날짜를 기준으로 주기와 일정이 계산됩니다. 나중에 AI 상담에서 수정할 수 있어요.
        </div>
      </div>

      <button
        onClick={goNext}
        disabled={!form.periodDate}
        style={form.periodDate ? { ...btnPrimary, marginTop: 8 } : { ...disabledBtn, marginTop: 8 }}
      >
        다음
      </button>
    </StepLayout>
  );

  // ══════════════════════════════
  // STEP 3: Branching
  //   natural → cycle length
  //   medical → procedure selection
  // ══════════════════════════════
  if (step === 3) {
    if (form.mode === 'natural') {
      // Cycle length selection
      const canNext = !!form.cycle;
      const nextTarget = consent.notification ? phoneStep : doneStep;
      return (
        <StepLayout
          tag="주기 정보"
          question="평균 생리 주기는 어떻게 되나요?"
          subtitle="생리 시작일부터 다음 생리 시작 전날까지의 기간이에요."
          show={show}
          onBack={() => goTo(2)}
          onSkip={() => onGuest && onGuest(form.mode)}
          progress={4}
          totalSteps={totalSteps}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {CYCLE_OPTIONS.map((c, i) => (
              <RadioCard
                key={c.value}
                selected={form.cycle === c.value}
                label={c.label}
                show={show}
                delay={i * 60}
                onClick={() => update('cycle', c.value)}
              />
            ))}
          </div>

          <button
            onClick={() => goTo(nextTarget)}
            disabled={!canNext}
            style={canNext ? { ...btnPrimary, marginTop: 32 } : { ...disabledBtn, marginTop: 32 }}
          >
            다음
          </button>
        </StepLayout>
      );
    }

    // Medical: procedure selection
    const canNext = !!form.procedure;
    return (
      <StepLayout
        tag="병원 시술 관리"
        question="현재 진행 중인 시술을 선택해 주세요"
        subtitle="일정과 알림을 맞춤 세팅해 드릴게요"
        show={show}
        onBack={() => goTo(2)}
        onSkip={() => onGuest && onGuest(form.mode)}
        progress={4}
        totalSteps={totalSteps}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {PROCEDURE_OPTIONS.map((p, i) => (
            <RadioCard
              key={p.id}
              selected={form.procedure === p.id}
              label={p.label}
              desc={p.desc}
              show={show}
              delay={i * 60}
              onClick={() => {
                update('procedure', p.id);
                // Reset downstream when procedure changes
                update('protocol', '');
                update('stage', '');
              }}
            />
          ))}
        </div>

        <button
          onClick={() => {
            if (form.procedure === 'consult') {
              goTo(consent.notification ? phoneStep : doneStep);
            } else {
              goNext();
            }
          }}
          disabled={!canNext}
          style={canNext ? { ...btnPrimary, marginTop: 32 } : { ...disabledBtn, marginTop: 32 }}
        >
          다음
        </button>
      </StepLayout>
    );
  }

  // ══════════════════════════════
  // STEP 4: Depends on procedure
  //   timing → cycle length → done
  //   iui → IUI stage → done
  //   ivf → protocol → step 5
  // ══════════════════════════════
  if (step === 4 && form.mode === 'medical') {
    if (form.procedure === 'timing') {
      // Cycle length (same as natural)
      const canNext = !!form.cycle;
      const nextTarget = consent.notification ? phoneStep : doneStep;
      return (
        <StepLayout
          tag="주기 정보"
          question="평균 생리 주기는 어떻게 되나요?"
          subtitle="생리 시작일부터 다음 생리 시작 전날까지의 기간이에요."
          show={show}
          onBack={() => goTo(3)}
          onSkip={() => onGuest && onGuest(form.mode)}
          progress={5}
          totalSteps={totalSteps}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {CYCLE_OPTIONS.map((c, i) => (
              <RadioCard
                key={c.value}
                selected={form.cycle === c.value}
                label={c.label}
                show={show}
                delay={i * 60}
                onClick={() => update('cycle', c.value)}
              />
            ))}
          </div>

          <button
            onClick={() => goTo(nextTarget)}
            disabled={!canNext}
            style={canNext ? { ...btnPrimary, marginTop: 32 } : { ...disabledBtn, marginTop: 32 }}
          >
            다음
          </button>
        </StepLayout>
      );
    }

    if (form.procedure === 'iui') {
      // IUI sub-stage
      const canNext = !!form.stage;
      const nextTarget = consent.notification ? phoneStep : doneStep;
      return (
        <StepLayout
          tag="인공수정 (IUI)"
          question="현재 어떤 단계에 계신가요?"
          subtitle="단계에 맞는 정보와 알림을 드릴게요"
          show={show}
          onBack={() => goTo(3)}
          progress={5}
          totalSteps={totalSteps}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {IUI_STAGE_OPTIONS.map((s, i) => (
              <RadioCard
                key={s.value}
                selected={form.stage === s.value}
                label={s.label}
                desc={s.desc}
                show={show}
                delay={i * 60}
                onClick={() => update('stage', s.value)}
              />
            ))}
          </div>

          <button
            onClick={() => goTo(nextTarget)}
            disabled={!canNext}
            style={canNext ? { ...btnPrimary, marginTop: 32 } : { ...disabledBtn, marginTop: 32 }}
          >
            다음
          </button>
        </StepLayout>
      );
    }

    if (form.procedure === 'ivf') {
      // IVF protocol
      const canNext = !!form.protocol;
      return (
        <StepLayout
          tag="체외수정 (IVF)"
          question="과배란 유도 프로토콜을 알고 계신가요?"
          subtitle="모르시면 '잘 모르겠어요'를 선택하셔도 괜찮아요"
          show={show}
          onBack={() => goTo(3)}
          progress={5}
          totalSteps={totalSteps}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {IVF_PROTOCOL_OPTIONS.map((p, i) => (
              <RadioCard
                key={p.value}
                selected={form.protocol === p.value}
                label={p.label}
                show={show}
                delay={i * 60}
                onClick={() => update('protocol', p.value)}
              />
            ))}
          </div>

          <button
            onClick={goNext}
            disabled={!canNext}
            style={canNext ? { ...btnPrimary, marginTop: 32 } : { ...disabledBtn, marginTop: 32 }}
          >
            다음
          </button>
        </StepLayout>
      );
    }
  }

  // ══════════════════════════════
  // STEP 5: IVF stage selection
  // ══════════════════════════════
  if (step === 5 && form.mode === 'medical' && form.procedure === 'ivf') {
    const canNext = !!form.stage;
    const nextTarget = consent.notification ? phoneStep : doneStep;
    return (
      <StepLayout
        tag="체외수정 (IVF)"
        question="현재 어떤 단계에 계신가요?"
        subtitle="단계에 맞는 일정과 케어를 세팅해 드릴게요"
        show={show}
        onBack={() => goTo(4)}
        onSkip={() => onGuest && onGuest(form.mode)}
        progress={6}
        totalSteps={totalSteps}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {IVF_STAGE_OPTIONS.map((s, i) => (
            <RadioCard
              key={s.value}
              selected={form.stage === s.value}
              label={s.label}
              desc={s.desc}
              show={show}
              delay={i * 60}
              onClick={() => update('stage', s.value)}
            />
          ))}
        </div>

        <button
          onClick={() => goTo(nextTarget)}
          disabled={!canNext}
          style={canNext ? { ...btnPrimary, marginTop: 32 } : { ...disabledBtn, marginTop: 32 }}
        >
          다음
        </button>
      </StepLayout>
    );
  }

  // ══════════════════════════════
  // PHONE STEP (dynamic position)
  // ══════════════════════════════
  if (consent.notification && step === phoneStep) {
    const canNext = form.phone.length >= 10;
    return (
      <StepLayout
        tag="알림 설정"
        question="알림을 받을 전화번호를 알려주세요"
        subtitle="카카오톡 알림톡으로 복약 리마인더와 메디컬 체크 알림을 보내드려요."
        show={show}
        onBack={() => goTo(phoneStep - 1)}
        onSkip={() => goTo(doneStep)}
        progress={phoneStep}
        totalSteps={totalSteps}
      >
        <div style={{ marginBottom: 24 }}>
          <input
            value={form.phone}
            onChange={e => update('phone', e.target.value.replace(/[^0-9]/g, ''))}
            placeholder="01012345678"
            maxLength={11}
            inputMode="tel"
            style={{
              ...inputStyle,
              fontSize: 16,
              padding: '14px 16px',
              textAlign: 'center',
              letterSpacing: 2,
            }}
          />
          <div style={{ fontSize: 11, color: theme.textSub, marginTop: 8, textAlign: 'center' }}>
            '-' 없이 숫자만 입력해주세요
          </div>
        </div>

        <button
          onClick={() => goTo(doneStep)}
          disabled={!canNext}
          style={canNext ? { ...btnPrimary, marginTop: 8 } : { ...disabledBtn, marginTop: 8 }}
        >
          다음
        </button>
      </StepLayout>
    );
  }

  // ══════════════════════════════
  // DONE screen
  // ══════════════════════════════
  if (step === doneStep) {
    const msg = getDoneMessage(form);
    // figure out what step to go back to — 동의 화면(step 1)으로
    const prevStep = 1;

    return (
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '40px 24px', textAlign: 'center',
      }}>
        <Fade show={show}>
          <div style={{
            fontSize: 64, marginBottom: 20,
            filter: 'drop-shadow(0 4px 12px rgba(124,106,175,0.15))',
          }}>{msg.emoji}</div>
          <h2 style={{
            fontSize: 22, fontWeight: 700, color: theme.text,
            margin: '0 0 12px', lineHeight: 1.4, letterSpacing: -0.3,
          }}>{msg.title}</h2>
          <p style={{
            fontSize: 15, color: theme.textSub, lineHeight: 1.7,
            margin: '0 0 40px', whiteSpace: 'pre-line',
          }}>{msg.sub}</p>

          {/* 닉네임 입력 */}
          <div style={{ width: '100%', maxWidth: 320, marginBottom: 24 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: theme.text, display: 'block', marginBottom: 6, textAlign: 'left' }}>닉네임</label>
            <input
              value={form.nickname}
              onChange={e => update('nickname', e.target.value)}
              placeholder="2~12자"
              maxLength={12}
              style={{ ...inputStyle, textAlign: 'center', fontSize: 16, fontWeight: 600 }}
            />
            {form.nickname.length > 0 && form.nickname.length < 2 && (
              <div style={{ fontSize: 12, color: '#C44', marginTop: 4 }}>닉네임은 2자 이상이어야 해요.</div>
            )}
          </div>

          {/* Summary chips */}
          <div style={{
            display: 'flex', flexWrap: 'wrap', gap: 8,
            justifyContent: 'center', marginBottom: 40,
          }}>
            {form.mode && (
              <span style={{
                padding: '6px 14px', borderRadius: 20,
                background: theme.primaryLight, color: theme.primary,
                fontSize: 13, fontWeight: 500,
              }}>
                {form.mode === 'natural' ? '자연임신 준비' : '병원 시술'}
              </span>
            )}
            {form.periodDate && (
              <span style={{
                padding: '6px 14px', borderRadius: 20,
                background: theme.primaryLight, color: theme.primary,
                fontSize: 13, fontWeight: 500,
              }}>
                생리일 {form.periodDate}
              </span>
            )}
            {form.cycle && (
              <span style={{
                padding: '6px 14px', borderRadius: 20,
                background: theme.primaryLight, color: theme.primary,
                fontSize: 13, fontWeight: 500,
              }}>
                주기 {CYCLE_OPTIONS.find(c => c.value === form.cycle)?.label || form.cycle}
              </span>
            )}
            {form.procedure && form.mode === 'medical' && (
              <span style={{
                padding: '6px 14px', borderRadius: 20,
                background: theme.primaryLight, color: theme.primary,
                fontSize: 13, fontWeight: 500,
              }}>
                {PROCEDURE_OPTIONS.find(p => p.id === form.procedure)?.label || form.procedure}
              </span>
            )}
          </div>

          <button onClick={handleComplete} disabled={!form.nickname || form.nickname.trim().length < 2} style={{
            ...(!form.nickname || form.nickname.trim().length < 2 ? disabledBtn : btnPrimary),
            maxWidth: 360,
            fontSize: 16,
            padding: '16px 0',
          }}>
            라일 시작하기 →
          </button>

          <button onClick={() => goTo(prevStep)} style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'none', border: 'none',
            fontSize: 14, color: theme.textSub, cursor: 'pointer',
            padding: '16px 0 8px', margin: '0 auto',
          }}>
            <span style={{ fontSize: 16 }}>←</span> 이전으로
          </button>
          {onGuest && <button onClick={() => onGuest(form.mode)} style={{
            display: 'block', background: 'none', border: 'none', fontSize: 13,
            color: theme.textSub, cursor: 'pointer', padding: '8px 0 0', margin: '0 auto',
          }}>건너뛰기</button>}
        </Fade>
      </div>
    );
  }

  // Fallback: shouldn't reach here, but just in case redirect to done
  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <button onClick={() => goTo(doneStep)} style={btnPrimary}>
        계속하기
      </button>
    </div>
  );
}
