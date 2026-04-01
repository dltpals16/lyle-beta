// 시술 단계별 타임라인 템플릿
// 출처: timeline_extension.json (v1.3.1), 난임 가이드북, 리플렛, ASRM/ESHRE/대한생식의학회 가이드라인
// IVF 프로토콜별 출처: 서울아이앤여성의원 (in-fertilityclinic.com), 송파마리아 이재은
// 생리 시작일 = Day 1 기준
// 가임기: 배란 3~5일 전 ~ 배란 후 2~3일 (건강보험공단 기준)

export const STAGE_TIMELINES = {
  prep: [
    { day: 1, label: '난임 상담 예약', desc: '산부인과 또는 난임 전문 병원에서 첫 상담을 받아요.', icon: '🏥', week: '1주차' },
    { day: 2, label: '기초 검사 (여성)', desc: '호르몬 검사(FSH, LH, AMH, E2), 초음파, 자궁난관조영술(HSG) 등을 진행해요.', icon: '🔬', week: '1~2주차' },
    { day: 3, label: '기초 검사 (남성)', desc: '정액검사를 진행해요. 검사 2~3일 전부터 금욕이 필요해요.', icon: '🔬', week: '1~2주차' },
    { day: 4, label: '검사 결과 상담', desc: '검사 결과를 바탕으로 원인을 파악하고 치료 방향을 상담해요.', icon: '📋', week: '2~3주차' },
    { day: 5, label: '치료 계획 수립', desc: '시술 방법(타이밍/IUI/IVF) 및 일정을 결정해요. 필요시 추가 검사를 진행해요.', icon: '📝', week: '3~4주차' },
  ],

  timing: [
    { day: 1, label: '생리 시작', desc: '생리 시작에 맞추어 시술 주기가 시작돼요.', icon: '🏥' },
    { day: 3, label: '배란유도제 복용', desc: '클로미펜 또는 페마라를 복용해요. 생리 3~5일째부터 5일간 복용해요.', icon: '💊' },
    { day: 10, label: '난포 모니터링', desc: '초음파로 난포 크기를 확인해요. 18~20mm 이상이면 배란이 임박해요.', icon: '📊' },
    { day: 12, label: '배란 및 가임기', desc: '배란을 확인한 후 성관계를 가져요. hCG 트리거 주사를 맞을 수도 있어요. 배란 후 초음파로 배란 여부를 확인하고, 프로게스테론 보충이 시작될 수 있어요.', icon: '💜' },
    { day: 28, label: '임신 판정', desc: '혈액검사(hCG)로 임신 여부를 확인해요. 임테기 사용도 가능해요.', icon: '🎯' },
  ],

  iui: [
    { day: 1, label: '생리 시작', desc: '생리 시작에 맞추어 시술 주기가 시작돼요.', icon: '🏥' },
    { day: 2, label: '기초 검사 및 과배란 유도', desc: '혈액검사 및 초음파를 진행하고, 배란 유도제(클로미펜/페마라/주사)를 시작해요.', icon: '🔬' },
    { day: 9, label: '난포 모니터링', desc: '초음파로 난포 성장을 확인하고, 주사 용량을 조절해요. 난포 크기를 최종 확인하고 트리거 주사 시점을 결정해요.', icon: '📊' },
    { day: 13, label: '인공수정 시술', desc: '정제된 정자를 자궁 내에 주입해요. 시술은 5~10분 정도이고 통증은 거의 없어요. 이후 일상생활은 가능하지만, 통목욕이나 사우나는 피하는 게 좋아요.', icon: '🔬' },
    { day: 27, label: '임신 판정', desc: '혈액검사(hCG)로 임신 여부를 확인해요.', icon: '🎯' },
  ],

  ivf_long: [
    { day: -7, label: '조기배란 억제 시작', desc: 'GnRH 작용제(루프린 등) 피하주사를 시작해요. 이전 주기 21일째부터 시작해요.', icon: '💉' },
    { day: 1, label: '생리 시작 및 검사', desc: '생리 시작에 맞추어 시술 주기가 시작돼요. 혈액검사(FSH, E2) 및 초음파로 난소 억제 상태를 확인해요.', icon: '🏥' },
    { day: 5, label: '과배란 유도', desc: '고날에프/퓨레곤(rFSH) 주사를 추가해요. GnRH 작용제와 병행하며, 매일 같은 시간에 투약해요.', icon: '💉' },
    { day: 9, label: '난포 모니터링', desc: '초음파로 난포 성장을 확인하고, 주사 용량을 조절해요. 난포가 17~18mm 이상이면 채취 일정이 잡혀요.', icon: '📊' },
    { day: 13, label: '난자 채취', desc: '수면마취 하에 난자를 채취해요. 20~30분 정도 소요돼요.', icon: '🥚' },
    { day: 18, label: '배아 이식', desc: '수정 및 배양을 거쳐 배아를 자궁에 이식해요. 남은 배아는 동결 보관해요.', icon: '🌱' },
    { day: 19, label: '황체기 보강', desc: '프로게스테론 주사 또는 크리논 겔을 사용해요. 임신 8~10주까지 지속해요.', icon: '💊' },
    { day: 30, label: '임신 판정', desc: '배아 이식 후 약 10~15일 뒤 혈액검사(hCG)로 임신 여부를 확인해요.', icon: '🎯' },
  ],

  ivf_short: [
    { day: 1, label: '생리 시작 및 주사 시작', desc: '생리 시작에 맞추어 시술 주기가 시작돼요. GnRH 작용제와 rFSH 주사를 동시에 시작해요.', icon: '🏥' },
    { day: 8, label: '난포 모니터링', desc: '초음파로 난포 성장을 확인하고, 주사 용량을 조절해요. 난포가 17~18mm 이상이면 채취 일정이 잡혀요.', icon: '📊' },
    { day: 13, label: '난자 채취', desc: '수면마취 하에 난자를 채취해요. 20~30분 정도 소요돼요.', icon: '🥚' },
    { day: 18, label: '배아 이식', desc: '수정 및 배양을 거쳐 배아를 자궁에 이식해요. 남은 배아는 동결 보관해요.', icon: '🌱' },
    { day: 19, label: '황체기 보강', desc: '프로게스테론 주사 또는 크리논 겔을 사용해요. 임신 8~10주까지 지속해요.', icon: '💊' },
    { day: 30, label: '임신 판정', desc: '배아 이식 후 약 10~15일 뒤 혈액검사(hCG)로 임신 여부를 확인해요.', icon: '🎯' },
  ],

  ivf_antagonist: [
    { day: 1, label: '생리 시작 및 검사', desc: '생리 시작에 맞추어 시술 주기가 시작돼요. 혈액검사(AMH, FSH, E2) 및 초음파로 난소 기능을 확인해요.', icon: '🏥' },
    { day: 3, label: '과배란 유도', desc: '고날에프/퓨레곤(rFSH) 주사를 시작해요. 매일 같은 시간에 투약해요.', icon: '💉' },
    { day: 8, label: '모니터링 및 길항제', desc: '초음파로 난포를 확인하고, 조기 배란 방지를 위해 길항제를 추가해요. 난포가 17~18mm 이상이면 채취 일정이 잡혀요.', icon: '📊' },
    { day: 13, label: '난자 채취', desc: '수면마취 하에 난자를 채취해요. 20~30분 정도 소요돼요.', icon: '🥚' },
    { day: 18, label: '배아 이식', desc: '수정 및 배양을 거쳐 배아를 자궁에 이식해요. 남은 배아는 동결 보관해요.', icon: '🌱' },
    { day: 19, label: '황체기 보강', desc: '프로게스테론 주사 또는 크리논 겔을 사용해요. 임신 8~10주까지 지속해요.', icon: '💊' },
    { day: 30, label: '임신 판정', desc: '배아 이식 후 약 10~15일 뒤 혈액검사(hCG)로 임신 여부를 확인해요.', icon: '🎯' },
  ],

  ivf_natural: [
    { day: 1, label: '생리 시작 및 검사', desc: '생리 시작에 맞추어 시술 주기가 시작돼요. 초음파로 동난포 갯수와 크기를 확인하고, 기초 호르몬검사도 진행해요.', icon: '🏥' },
    { day: 9, label: '난포 모니터링', desc: '초음파와 혈액검사로 난포 성장과 성숙도를 확인해요. 난포가 성숙하면 채취 일정이 잡혀요.', icon: '📊' },
    { day: 13, label: '난자 채취', desc: '난자를 채취해요. 자연주기는 보통 1~2개 난자를 채취해요.', icon: '🥚' },
    { day: 16, label: '배아 이식', desc: '수정 확인 후 배아를 이식해요. 준비가 안 되면 동결 후 다음 주기에 이식할 수도 있어요.', icon: '🌱' },
    { day: 17, label: '황체기 보강', desc: '프로게스테론을 보충해요. 임신 확인까지 지속해요.', icon: '💊' },
    { day: 28, label: '임신 판정', desc: '배아 이식 후 약 10~15일 뒤 혈액검사(hCG)로 임신 여부를 확인해요.', icon: '🎯' },
  ],

  ivf: [
    { day: 1, label: '생리 시작 및 검사', desc: '생리 시작에 맞추어 시술 주기가 시작돼요. 혈액검사(AMH, FSH, E2) 및 초음파로 난소 기능을 확인해요.', icon: '🏥' },
    { day: 3, label: '과배란 유도', desc: '고날에프/퓨레곤(rFSH) 주사를 시작해요. 매일 같은 시간에 투약해요.', icon: '💉' },
    { day: 8, label: '난포 모니터링', desc: '초음파로 난포를 확인하고, 조기배란 억제 주사를 시작할 수 있어요. 난포가 17~18mm 이상이면 채취 일정이 잡혀요.', icon: '📊' },
    { day: 13, label: '난자 채취', desc: '수면마취 하에 난자를 채취해요. 20~30분 정도 소요돼요.', icon: '🥚' },
    { day: 18, label: '배아 이식', desc: '수정 및 배양을 거쳐 배아를 자궁에 이식해요. 남은 배아는 동결 보관해요.', icon: '🌱' },
    { day: 19, label: '황체기 보강', desc: '프로게스테론 주사 또는 크리논 겔을 사용해요. 임신 8~10주까지 지속해요.', icon: '💊' },
    { day: 30, label: '임신 판정', desc: '배아 이식 후 약 10~15일 뒤 혈액검사(hCG)로 임신 여부를 확인해요.', icon: '🎯' },
  ],

  fet: [
    { day: 1, label: '생리 시작 및 검사', desc: '생리 시작에 맞추어 이식 주기가 시작돼요. 혈액검사 및 초음파를 통해 자궁내막 상태를 확인해요.', icon: '🏥' },
    { day: 3, label: '에스트로겐 복용', desc: '에스트로겐 제제를 복용하며 자궁내막을 두껍게 만들어요.', icon: '💊' },
    { day: 10, label: '내막 모니터링', desc: '초음파로 자궁내막 두께를 확인해요. 7mm 이상이 필요하고 8~10mm가 최적이에요.', icon: '📊' },
    { day: 14, label: '프로게스테론', desc: '내막이 충분히 두꺼워지면 프로게스테론을 시작해요. 이식일까지 꾸준히 복용해요.', icon: '💊' },
    { day: 19, label: '배아 이식', desc: '프로게스테론 5일째에 동결 배아를 해동하여 자궁에 이식해요. 마취 없이 진행돼요. 이후 무리한 활동은 자제해요.', icon: '❄️' },
    { day: 31, label: '임신 판정', desc: '배아 이식 후 약 10~15일 뒤 혈액검사(hCG)로 임신 여부를 확인해요.', icon: '🎯' },
  ],
};

// 오늘이 시술 몇 일차인지 계산
export function calculateDayInCycle(periodDateStr) {
  if (!periodDateStr) return null;
  const parts = periodDateStr.split('-').map(Number);
  if (parts.length !== 3 || parts.some(isNaN)) return null;

  const [year, month, day] = parts;
  const periodDate = new Date(year, month - 1, day);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  periodDate.setHours(0, 0, 0, 0);

  const diffMs = today - periodDate;
  if (diffMs < 0) return null; // 미래 날짜
  return Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1; // Day 1부터 시작
}

// 프로토콜에 따른 IVF 타임라인 키 결정
const IVF_PROTOCOL_MAP = {
  long: 'ivf_long',
  short: 'ivf_short',
  antagonist: 'ivf_antagonist',
  natural: 'ivf_natural',
  unknown: 'ivf',
};

function resolveTimelineKey(stage, protocol, ivfPhase) {
  // ivfPhase가 'fet'이면 FET 타임라인 사용
  if (stage === 'ivf' && ivfPhase === 'fet') return 'fet';
  if (stage === 'ivf' && protocol && IVF_PROTOCOL_MAP[protocol]) {
    return IVF_PROTOCOL_MAP[protocol];
  }
  return stage;
}

// 타임라인 데이터에 현재 상태(done/current/upcoming) 부여
export function getTimelineWithStatus(stage, periodDateStr, cycle, protocol, currentPhase, ivfPhase) {
  const key = resolveTimelineKey(stage, protocol, ivfPhase);
  const template = STAGE_TIMELINES[key];
  if (!template) return [];

  // 준비 단계이거나 cycle 0 (아직 시작 전)이면 모두 upcoming
  if (stage === 'prep' || cycle === 0) {
    return template.map(item => ({ ...item, status: 'upcoming' }));
  }

  // currentPhase가 있으면 label 매칭으로 현재 위치 결정
  if (currentPhase) {
    const phaseNorm = currentPhase.trim().toLowerCase().replace(/\s+/g, '');
    const matchIdx = template.findIndex(item => {
      const labelNorm = item.label.toLowerCase().replace(/\s+/g, '');
      return labelNorm.includes(phaseNorm) || phaseNorm.includes(labelNorm) ||
        // 핵심 키워드 매칭 (예: "에스트로겐" + "시작")
        phaseNorm.split(/\s+/).filter(w => w.length >= 2).every(w => item.label.toLowerCase().includes(w));
    });
    if (matchIdx >= 0) {
      return template.map((item, i) => ({
        ...item,
        status: i < matchIdx ? 'done' : i === matchIdx ? 'current' : 'upcoming',
        _phaseMatchDay: template[matchIdx].day,
      }));
    }
  }

  // fallback: 날짜 기반 계산
  const currentDay = calculateDayInCycle(periodDateStr);
  if (currentDay === null) {
    return template.map(item => ({ ...item, status: 'upcoming' }));
  }

  return template.map(item => {
    let status;
    if (currentDay >= item.day) {
      const nextItem = template.find(t => t.day > item.day);
      if (!nextItem || currentDay < nextItem.day) {
        status = 'current';
      } else {
        status = 'done';
      }
    } else {
      status = 'upcoming';
    }
    return { ...item, status };
  });
}

// 현재 단계 요약 정보 (홈 화면용)
export function getCurrentStageInfo(stage, periodDateStr, cycle, protocol, currentPhase, ivfPhase) {
  const timeline = getTimelineWithStatus(stage, periodDateStr, cycle, protocol, currentPhase, ivfPhase);

  // 준비 단계이거나 cycle 0 (아직 시작 전)
  if (stage === 'prep' || cycle === 0) {
    const stageName = stage === 'prep' ? '검사/준비' :
      { timing: '배란기 성관계', iui: '인공수정(IUI)', ivf: '체외수정(IVF)', fet: '동결배아이식(FET)' }[stage] || '시술';
    return {
      dayText: '준비 중',
      desc: stage === 'prep'
        ? '난임 검사를 진행하고 치료 계획을 세우는 단계예요.'
        : `${stageName} 시술 예정이에요. 시작하면 타임라인이 활성화됩니다.`,
      currentStep: null,
      nextStep: timeline[0] || null,
    };
  }

  const currentDay = calculateDayInCycle(periodDateStr);

  if (currentDay === null) {
    return {
      dayText: '시술 준비 중',
      desc: '생리가 시작되면 시술 주기가 시작됩니다.',
      currentStep: null,
      nextStep: timeline[0] || null,
    };
  }

  const currentStep = timeline.find(item => item.status === 'current');
  const nextStep = timeline.find(item => item.status === 'upcoming');
  const lastStep = timeline[timeline.length - 1];

  // 타임라인이 비어있는 경우 (자연임신 등)
  if (!lastStep) {
    return {
      dayText: `${currentDay}일차`,
      desc: '',
      currentStep: null,
      nextStep: null,
    };
  }

  // 주기 완료 확인
  if (currentDay > lastStep.day) {
    return {
      dayText: '판정 대기 중',
      desc: '임신 판정일이 지났어요.',
      currentStep: lastStep,
      nextStep: null,
      pastJudgment: true,
    };
  }

  // 프로그레스 계산
  const totalDays = lastStep.day || 30;
  const progressPct = Math.round((currentDay / totalDays) * 100);

  // 다음 단계까지 남은 일수
  if (nextStep) {
    nextStep.daysLeft = Math.max(0, nextStep.day - currentDay);
  }

  // 주요 마일스톤 5개만 추출 (첫 단계, 마지막 단계 포함 + 중간에서 균등하게)
  const keyIndices = [0];
  const step = Math.max(1, Math.floor((timeline.length - 1) / 3));
  for (let i = step; i < timeline.length - 1; i += step) {
    if (keyIndices.length < 4) keyIndices.push(i);
  }
  keyIndices.push(timeline.length - 1);
  const milestones = [...new Set(keyIndices)].map(i => ({
    label: timeline[i].label,
    pct: Math.round((timeline[i].day / totalDays) * 100),
    status: timeline[i].status,
  }));

  return {
    dayText: `${currentDay}일차`,
    desc: currentStep ? currentStep.desc : '다음 단계를 기다리고 있어요.',
    currentStep,
    nextStep,
    progressPct,
    milestones,
    timeline,
    totalDays,
    currentDay,
  };
}

// 오늘 할 일 생성 (현재 단계 기반)
export function getTodayTasks(stage, periodDateStr, cycle, protocol, ivfPhase) {
  const timeline = getTimelineWithStatus(stage, periodDateStr, cycle, protocol, null, ivfPhase);
  const currentDay = calculateDayInCycle(periodDateStr);
  const tasks = [];

  // 준비 단계이거나 cycle 0 (아직 시작 전)
  if (stage === 'prep' || cycle === 0) {
    return [
      { text: '난임 전문 병원 알아보기', done: false },
      { text: '기초 검사 일정 확인하기', done: false },
      { text: '감정일기 기록하기', done: false },
    ];
  }

  if (currentDay === null) {
    return [{ text: '생리 시작일을 기다리고 있어요', done: false }];
  }

  const currentStep = timeline.find(item => item.status === 'current');
  const nextStep = timeline.find(item => item.status === 'upcoming');

  if (currentStep) {
    tasks.push({ text: currentStep.label, done: true });
  }

  // 주사 맞는 기간인지 확인
  const stageData = STAGE_TIMELINES[resolveTimelineKey(stage, protocol, ivfPhase)];
  const injectionSteps = stageData.filter(s =>
    s.icon === '💉' || s.desc.includes('주사')
  );
  const isInjectionPeriod = injectionSteps.some(s => {
    const nextS = stageData.find(t => t.day > s.day);
    return currentDay >= s.day && (!nextS || currentDay < nextS.day + 2);
  });

  if (isInjectionPeriod && (stage === 'iui' || stage === 'ivf')) {
    tasks.push({ text: '오늘 호르몬 주사 투약 (같은 시간)', done: false });
  }

  tasks.push({ text: '수분 섭취 1.5L 이상', done: false });
  tasks.push({ text: '감정일기 기록하기', done: false });

  if (nextStep && nextStep.day - currentDay <= 2) {
    tasks.push({ text: `${nextStep.label} 준비하기 (D-${nextStep.day - currentDay})`, done: false });
  }

  return tasks;
}
