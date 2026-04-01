const medicalTheme = {
  primary: '#7C6AAF',
  primaryLight: '#E5DFF5',
  primaryBg: '#F6F4FB',
  primaryDark: '#5A4B8A',
  accent: '#A594D0',
  text: '#2A2440',
  textSub: '#8C839E',
  bg: '#F8F6FD',
  card: '#FFFFFF',
  border: '#EDEAF3',
  success: '#6EB89A',
  warning: '#D4A84B',
  radius: 14,
  font: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
};

const naturalTheme = {
  ...medicalTheme,
  primary: '#E8724A',
  primaryLight: '#FFCCB8',
  primaryBg: '#FFF0EC',
  primaryDark: '#C9572E',
  accent: '#9B8CD9',
  bg: '#FFF8F5',
  border: '#FFD4C2',
};

// 기본값은 medical (기존 호환성)
export const theme = medicalTheme;
export const naturalPalette = naturalTheme;
export function getTheme(mode) {
  return mode === 'natural' ? naturalTheme : medicalTheme;
}

export const inputStyle = {
  width: '100%',
  padding: '13px 16px',
  borderRadius: medicalTheme.radius,
  border: `1.5px solid ${medicalTheme.border}`,
  fontSize: 15,
  color: medicalTheme.text,
  background: medicalTheme.card,
  outline: 'none',
  boxSizing: 'border-box',
  transition: 'border-color 0.2s',
};

export const labelStyle = {
  fontSize: 13,
  fontWeight: 600,
  color: medicalTheme.text,
  display: 'block',
  marginBottom: 7,
};

export const btnPrimary = {
  width: '100%',
  padding: '14px 0',
  borderRadius: medicalTheme.radius,
  background: `linear-gradient(135deg, ${medicalTheme.primary}, ${medicalTheme.primaryDark})`,
  color: '#fff',
  fontSize: 15,
  fontWeight: 700,
  border: 'none',
  cursor: 'pointer',
  boxShadow: '0 4px 18px rgba(124,106,175,0.25)',
  transition: 'transform 0.15s, box-shadow 0.15s',
};
