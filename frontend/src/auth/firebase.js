import { initializeApp } from 'firebase/app';
import { getAnalytics } from 'firebase/analytics';
import {
  getFirestore,
  doc,
  setDoc,
  getDoc,
  deleteDoc,
  serverTimestamp,
} from 'firebase/firestore';

// Firebase 설정 - .env 파일에서 읽어옴
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
export const db = getFirestore(app);

const STORAGE_KEY = 'lyle_nickname';

// ==================== 닉네임 중복 체크 ====================
export async function checkNickname(nickname) {
  const snap = await getDoc(doc(db, 'users', nickname));
  return snap.exists();
}

// ==================== 닉네임 회원가입 ====================
export async function registerWithNickname(nickname) {
  const exists = await checkNickname(nickname);
  if (exists) {
    throw { code: 'nickname/already-in-use', message: '이미 사용 중인 닉네임이에요.' };
  }

  await setDoc(doc(db, 'users', nickname), {
    displayName: nickname,
    createdAt: serverTimestamp(),
    onboardingComplete: false,
  });

  localStorage.setItem(STORAGE_KEY, nickname);
  return { uid: nickname, displayName: nickname };
}

// ==================== 닉네임 로그인 ====================
export async function loginWithNickname(nickname) {
  const exists = await checkNickname(nickname);
  if (!exists) {
    throw { code: 'nickname/not-found', message: '등록되지 않은 닉네임이에요.' };
  }

  localStorage.setItem(STORAGE_KEY, nickname);
  return { uid: nickname, displayName: nickname };
}

// ==================== 로그아웃 ====================
export async function logOut() {
  localStorage.removeItem(STORAGE_KEY);
}

// ==================== 닉네임 저장 (온보딩 완료 시) ====================
export function saveNickname(nickname) {
  localStorage.setItem(STORAGE_KEY, nickname);
}

// ==================== 현재 로그인된 사용자 확인 ====================
export function getSavedNickname() {
  return localStorage.getItem(STORAGE_KEY);
}

// ==================== 사용자 데이터 (Firestore) ====================

// 온보딩 데이터 저장
export async function saveUserProfile(uid, profileData) {
  await setDoc(doc(db, 'users', uid), {
    ...profileData,
    onboardingComplete: true,
    updatedAt: serverTimestamp(),
  }, { merge: true });
}

// 사용자 프로필 불러오기
export async function getUserProfile(uid) {
  const snap = await getDoc(doc(db, 'users', uid));
  return snap.exists() ? snap.data() : null;
}

// 감정일기 저장
export async function saveDiaryEntry(uid, entry) {
  const dateKey = new Date().toISOString().split('T')[0];
  await setDoc(doc(db, 'users', uid, 'diary', dateKey), {
    ...entry,
    createdAt: serverTimestamp(),
  });
}

// 대화 기록 저장
export async function saveChatMessages(uid, messages) {
  await setDoc(doc(db, 'users', uid, 'chat', 'latest'), {
    messages,
    updatedAt: serverTimestamp(),
  }, { merge: true });
}

// 대화 기록 불러오기
export async function getChatMessages(uid) {
  const snap = await getDoc(doc(db, 'users', uid, 'chat', 'latest'));
  return snap.exists() ? snap.data().messages : [];
}

// ==================== 회원 탈퇴 ====================
export async function deleteAccount() {
  const nickname = getSavedNickname();
  if (!nickname) throw new Error('로그인 상태가 아닙니다.');

  // Firestore 하위 컬렉션 문서 삭제
  try {
    await deleteDoc(doc(db, 'users', nickname, 'chat', 'latest'));
  } catch (e) { /* 없을 수 있음 */ }

  // Firestore 사용자 문서 삭제
  await deleteDoc(doc(db, 'users', nickname));

  // 로컬 로그아웃
  localStorage.removeItem(STORAGE_KEY);
}
