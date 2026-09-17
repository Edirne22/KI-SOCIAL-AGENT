import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type RaceCalendarProps = {
  series: string;
  track: string;
  dateRange: string;
};

export const RaceCalendar: React.FC<RaceCalendarProps> = ({
  series,
  track,
  dateRange,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 1. Overlay Red Line Animation (Frames 0-60: 0s - 2s)
  const lineProgress = interpolate(frame, [0, 50], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const lineOpacity = interpolate(frame, [50, 65], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // 2. Kinetic Typography (Series Title - Frames 10 onwards)
  const words = series.split(' ');

  // 3. Glitch Effect (Frames 45-50)
  const isGlitchFrame = frame >= 45 && frame <= 50;
  const glitchOffsetX = isGlitchFrame ? (frame % 2 === 0 ? 12 : -12) : 0;
  const glitchOffsetY = isGlitchFrame ? (frame % 3 === 0 ? -6 : 6) : 0;

  // 4. Bouncy TikTok Captions (Track: Frame 50+, Date: Frame 90+)
  const trackSpring = spring({
    frame: frame - 50,
    fps,
    config: { damping: 10, stiffness: 180 },
  });

  const dateSpring = spring({
    frame: frame - 90,
    fps,
    config: { damping: 12, stiffness: 200 },
  });

  // 5. Gentle Particle Rain (Frames 130-210)
  const particleCount = 25;
  const particles = Array.from({ length: particleCount }).map((_, i) => {
    const seedX = (i * 137.5) % 1080;
    const speed = 4 + (i % 5);
    const startFrame = 120 + (i % 20);
    const particleFrame = Math.max(0, frame - startFrame);
    const posY = (particleFrame * speed * 12) % 2000 - 80;
    const opacity = interpolate(frame, [130, 160], [0, 0.8], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });

    return {
      id: i,
      x: seedX,
      y: posY,
      size: 4 + (i % 6),
      opacity,
    };
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0a0a0c',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        color: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '60px',
        boxSizing: 'border-box',
        overflow: 'hidden',
      }}
    >
      {/* Background Subtle Red Glow */}
      <div
        style={{
          position: 'absolute',
          width: '800px',
          height: '800px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255, 0, 60, 0.15) 0%, rgba(0,0,0,0) 70%)',
          pointerEvents: 'none',
        }}
      />

      {/* 1. First 2s Overlay Animation: Animated Red Line Sweeping across */}
      {lineOpacity > 0 && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
            opacity: lineOpacity,
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: '20%',
              left: 0,
              height: '8px',
              width: `${lineProgress}%`,
              backgroundColor: '#ff003c',
              boxShadow: '0 0 25px #ff003c, 0 0 50px #ff003c',
              borderRadius: '4px',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: '20%',
              right: 0,
              height: '8px',
              width: `${lineProgress}%`,
              backgroundColor: '#ff003c',
              boxShadow: '0 0 25px #ff003c, 0 0 50px #ff003c',
              borderRadius: '4px',
            }}
          />
        </div>
      )}

      {/* Glitch RGB Split Layer */}
      {isGlitchFrame && (
        <div
          style={{
            position: 'absolute',
            top: `${glitchOffsetY}px`,
            left: `${glitchOffsetX}px`,
            color: 'rgba(0, 255, 255, 0.7)',
            fontSize: '90px',
            fontWeight: 900,
            letterSpacing: '4px',
            textTransform: 'uppercase',
            zIndex: 1,
            pointerEvents: 'none',
          }}
        >
          {series}
        </div>
      )}

      {/* 2. Kinetic Typography Title */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: '20px',
          marginBottom: '50px',
          zIndex: 2,
          transform: isGlitchFrame ? `translate(${-glitchOffsetX}px, ${-glitchOffsetY}px)` : 'none',
        }}
      >
        {words.map((word, index) => {
          const delay = 10 + index * 6;
          const wordSpring = spring({
            frame: frame - delay,
            fps,
            config: { damping: 12, stiffness: 220 },
          });

          return (
            <span
              key={index}
              style={{
                display: 'inline-block',
                fontSize: '85px',
                fontWeight: 900,
                textTransform: 'uppercase',
                letterSpacing: '6px',
                color: '#ffffff',
                textShadow: '0 4px 20px rgba(0,0,0,0.8)',
                transform: `scale(${Math.max(0, wordSpring)})`,
                opacity: wordSpring > 0 ? 1 : 0,
              }}
            >
              {word}
            </span>
          );
        })}
      </div>

      {/* 4. Bouncy TikTok-Style Captions: Track */}
      <div
        style={{
          transform: `scale(${Math.max(0, trackSpring)})`,
          opacity: frame >= 50 ? 1 : 0,
          backgroundColor: '#ff003c',
          color: '#ffffff',
          padding: '24px 48px',
          borderRadius: '24px',
          fontSize: '52px',
          fontWeight: 800,
          textAlign: 'center',
          textTransform: 'uppercase',
          boxShadow: '0 10px 30px rgba(255, 0, 60, 0.4)',
          marginBottom: '30px',
          maxWidth: '900px',
          zIndex: 2,
        }}
      >
        📍 {track}
      </div>

      {/* 4. Bouncy TikTok-Style Captions: Date Range */}
      <div
        style={{
          transform: `scale(${Math.max(0, dateSpring)})`,
          opacity: frame >= 90 ? 1 : 0,
          backgroundColor: '#16181d',
          border: '3px solid #ff003c',
          color: '#ffffff',
          padding: '20px 40px',
          borderRadius: '20px',
          fontSize: '44px',
          fontWeight: 700,
          textAlign: 'center',
          boxShadow: '0 8px 25px rgba(0, 0, 0, 0.6)',
          maxWidth: '850px',
          zIndex: 2,
        }}
      >
        🗓️ {dateRange}
      </div>

      {/* 5. Particle Rain Effect */}
      {frame >= 120 &&
        particles.map((p) => (
          <div
            key={p.id}
            style={{
              position: 'absolute',
              left: `${p.x}px`,
              top: `${p.y}px`,
              width: `${p.size}px`,
              height: `${p.size * 2}px`,
              backgroundColor: p.id % 2 === 0 ? '#ff003c' : '#ffffff',
              borderRadius: '50%',
              opacity: p.opacity,
              boxShadow: '0 0 10px #ff003c',
              pointerEvents: 'none',
            }}
          />
        ))}
    </AbsoluteFill>
  );
};
