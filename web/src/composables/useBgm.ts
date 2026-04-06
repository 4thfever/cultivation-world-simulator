import { watch, effectScope } from 'vue';
import { useSettingStore } from '../stores/setting';
import { withBasePublicPath } from '@/utils/assetUrls';
import { logWarn } from '@/utils/appError';

// 配置
const BGM_CONFIG = {
  splash: ['Eastminster.mp3'],
  map: [
    'Healing.mp3', 
    'Ishikari_20Lore.mp3', 
    'PerituneMaterial_Sakuya2.mp3', 
    'PerituneMaterial_Wuxia2_Guzheng_Pipa.mp3'
  ]
};

const FADE_DURATION = 2000; // 2 seconds crossfade

// 类型定义
type BgmType = 'splash' | 'map' | null;

// 模块级状态（单例模式）
let currentType: BgmType = null;
let activeType: BgmType = null;
let currentTrackIndex = 0; // 0 或 1
let tracks: HTMLAudioElement[] = [];
let initialized = false;
let bag: string[] = []; // 随机播放池
let currentSwitchId = 0; // 切换请求锁，用于防止并发竞争
let audioUnlocked = false;
let unlockListenersBound = false;

export function useBgm() {
    const settingStore = useSettingStore();

    function init() {
        if (initialized || typeof window === 'undefined') return;
        
        // 创建双轨道
        tracks = [new Audio(), new Audio()];
        tracks.forEach((t, i) => {
            t.loop = false; // 手动控制循环
            t.addEventListener('ended', () => onTrackEnded(i));
        });

        // 监听音量变化 - 使用 detached scope 防止被组件卸载时清理
        const scope = effectScope(true);
        scope.run(() => {
            watch(() => settingStore.bgmVolume, (newVol) => {
                updateVolume(newVol);
            });
        });

        // 初始化音量
        updateVolume(settingStore.bgmVolume);
        bindUnlockListeners();

        initialized = true;
    }

    function bindUnlockListeners() {
        if (unlockListenersBound) return;
        unlockListenersBound = true;

        const unlockAudio = () => {
            audioUnlocked = true;
            window.removeEventListener('pointerdown', unlockAudio);
            window.removeEventListener('keydown', unlockAudio);
            unlockListenersBound = false;

            if (currentType && activeType !== currentType) {
                void resumePendingPlayback();
            }
        };

        window.addEventListener('pointerdown', unlockAudio, { once: true });
        window.addEventListener('keydown', unlockAudio, { once: true });
    }

    async function resumePendingPlayback() {
        if (!currentType) return;
        const songName = getNextSong(currentType);
        await switchTrack(songName, activeType !== null);
    }

    function updateVolume(vol: number) {
        tracks.forEach(t => {
            // 如果正在淡入淡出，由动画循环控制音量，这里不打断
            if (!t.dataset.fading) {
                t.volume = vol;
            }
        });
    }

    // 轨道播放结束回调
    function onTrackEnded(index: number) {
        // 只处理当前活跃轨道的结束事件
        if (index !== currentTrackIndex) return;

        if (currentType === 'map') {
            // Map 模式：自然播放结束，切下一首（无需淡出旧的，因为已经结束了）
            playNextRandom(false); 
        } else if (currentType === 'splash') {
            // Splash 模式：单曲循环
            const track = tracks[index];
            track.currentTime = 0;
            track.play().catch(() => {
                activeType = null;
                bindUnlockListeners();
            });
        }
    }

    // 洗牌算法
    function shuffleBag() {
        if (bag.length === 0) {
            bag = [...BGM_CONFIG.map];
            // Fisher-Yates shuffle
            for (let i = bag.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [bag[i], bag[j]] = [bag[j], bag[i]];
            }
        }
    }

    function getNextSong(type: 'splash' | 'map'): string {
        if (type === 'splash') return BGM_CONFIG.splash[0];
        
        if (bag.length === 0) shuffleBag();
        return bag.pop()!;
    }

    // 主播放接口
    async function play(type: BgmType) {
        if (!initialized) init();
        
        // 如果传入 null 或者空，停止播放
        if (!type) {
            stop();
            return;
        }
        
        // 如果已经在播放同类型，忽略（保持当前播放）
        if (currentType === type && activeType === type) return;

        currentType = type;
        if (!audioUnlocked) {
            bindUnlockListeners();
            return;
        }

        const songName = getNextSong(type);
        // 切换类型时，旧轨道肯定在播放，需要淡出
        await switchTrack(songName, activeType !== null);
    }

    // 播放下一首随机曲目（Map模式专用）
    async function playNextRandom(crossfadeOutgoing: boolean = true) {
        if (currentType !== 'map') return;
        const songName = getNextSong('map');
        await switchTrack(songName, crossfadeOutgoing);
    }

    // 核心切歌逻辑
    async function switchTrack(songName: string, crossfadeOutgoing: boolean) {
        const url = withBasePublicPath(`bgm/${songName}`);
        const nextIndex = (currentTrackIndex + 1) % 2;
        const nextTrack = tracks[nextIndex];
        const currentTrack = tracks[currentTrackIndex];

        nextTrack.src = url;
        nextTrack.volume = 0; // 从静音开始淡入
        
        currentSwitchId++;
        const mySwitchId = currentSwitchId;
        
        try {
            await nextTrack.play();
            // 如果在等待 play 的过程中发起了新的切换，丢弃当前切换
            if (mySwitchId !== currentSwitchId) {
                nextTrack.pause();
                return;
            }
            performCrossfade(nextTrack, currentTrack, crossfadeOutgoing, mySwitchId);
            currentTrackIndex = nextIndex;
            activeType = currentType;
        } catch (e: unknown) {
            if (mySwitchId !== currentSwitchId) return;
            const errorName = e instanceof Error ? e.name : '';

            if (errorName === 'NotAllowedError') {
                activeType = null;
                audioUnlocked = false;
                currentTrack.pause();
                bindUnlockListeners();
                return;
            }

            if (errorName === 'AbortError') {
                return;
            }

            logWarn('Bgm switch track', e);
        }
    }

    // 淡入淡出动画
    function performCrossfade(fadeIn: HTMLAudioElement, fadeOut: HTMLAudioElement, fadeOutEnabled: boolean, mySwitchId: number) {
        const start = performance.now();
        // remove static targetVol capture
        
        fadeIn.dataset.fading = 'true';
        if (fadeOutEnabled) fadeOut.dataset.fading = 'true';

        function step(now: number) {
            // 如果有新的切歌请求，立刻中止当前淡入淡出动画
            if (mySwitchId !== currentSwitchId) {
                delete fadeIn.dataset.fading;
                if (fadeOutEnabled) delete fadeOut.dataset.fading;
                return;
            }

            const elapsed = now - start;
            const progress = Math.min(elapsed / FADE_DURATION, 1);
            const currentTargetVol = settingStore.bgmVolume; // Dynamic volume check

            // 淡入
            const newFadeInVol = progress * currentTargetVol;
            if (newFadeInVol >= 0 && newFadeInVol <= 1) {
                fadeIn.volume = newFadeInVol;
            }

            // 淡出
            if (fadeOutEnabled && !fadeOut.paused) {
                const newFadeOutVol = Math.max(0, (1 - progress) * currentTargetVol);
                if (newFadeOutVol >= 0 && newFadeOutVol <= 1) {
                    fadeOut.volume = newFadeOutVol;
                }
            }

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                // 动画结束
                delete fadeIn.dataset.fading;
                if (fadeOutEnabled) delete fadeOut.dataset.fading;
                
                if (fadeOutEnabled) {
                    fadeOut.pause();
                    fadeOut.currentTime = 0;
                }
                // 确保最终音量准确
                fadeIn.volume = settingStore.bgmVolume;
            }
        }
        requestAnimationFrame(step);
    }

    function stop() {
        if (!initialized) return;
        currentType = null;
        activeType = null;
        currentSwitchId++;
        const mySwitchId = currentSwitchId;

        tracks.forEach(t => {
             // 快速淡出后停止
             const startVol = t.volume;
             const start = performance.now();
             
             // 标记正在 fade 以避免 volume watcher 干扰
             t.dataset.fading = 'true';

             function fade(now: number) {
                 if (mySwitchId !== currentSwitchId) {
                     delete t.dataset.fading;
                     return;
                 }

                 const progress = Math.min((now - start) / 1000, 1); // 1秒淡出
                 t.volume = Math.max(0, startVol * (1 - progress));
                 
                 if (progress < 1) {
                     requestAnimationFrame(fade);
                 } else {
                     t.pause();
                     t.currentTime = 0;
                     delete t.dataset.fading;
                 }
             }
             if(!t.paused) requestAnimationFrame(fade);
        });
    }

    return { init, play, stop };
}
