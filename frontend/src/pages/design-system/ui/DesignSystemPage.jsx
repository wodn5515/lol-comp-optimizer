import { useState } from 'react';
import { Button, Card, CardHeader, CardContent, Input, ProgressBar } from '../../../shared/ui';
import { ChampionIcon, ChampionBadge } from '../../../entities/champion';
import { cn } from '../../../shared/lib/cn';
import { TIER_COLORS, TIER_ORDER } from '../../../shared/config/constants';

/* ───────────────────────── helpers ───────────────────────── */

function Section({ title, children }) {
  return (
    <section className="mb-16">
      <h2 className="text-lg font-bold text-gray-100 mb-1">{title}</h2>
      <div className="h-px bg-gray-800 mb-6" />
      {children}
    </section>
  );
}

function SubSection({ title, children }) {
  return (
    <div className="mb-8">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">{title}</h3>
      {children}
    </div>
  );
}

function Swatch({ name, color, textColor = 'text-gray-100' }) {
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div
        className="w-14 h-14 rounded-lg border border-gray-700"
        style={{ background: color }}
      />
      <span className="text-[10px] text-gray-400 text-center leading-tight">{name}</span>
      <span className="text-[10px] text-gray-600 font-mono">{color}</span>
    </div>
  );
}

/* ───────────────────────── page ───────────────────────── */

export function DesignSystemPage() {
  const [inputValue, setInputValue] = useState('');
  const [inputError, setInputError] = useState('');

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-5xl mx-auto px-6 py-12">

        {/* Header */}
        <header className="mb-16">
          <p className="text-xs font-medium text-amber-500 uppercase tracking-wider mb-2">
            Design System
          </p>
          <h1 className="text-3xl font-bold text-gray-100 mb-2">
            LoL Comp Optimizer
          </h1>
          <p className="text-gray-400 text-sm">
            컴포넌트 라이브러리 및 디자인 토큰 레퍼런스
          </p>
        </header>

        {/* ─── Colors ─── */}
        <Section title="Colors">
          <SubSection title="Background">
            <div className="flex flex-wrap gap-4">
              <Swatch name="Base" color="#030712" />
              <Swatch name="Surface" color="#111827" />
              <Swatch name="Elevated" color="#1f2937" />
              <Swatch name="Hover" color="#374151" />
            </div>
          </SubSection>

          <SubSection title="Border">
            <div className="flex flex-wrap gap-4">
              <Swatch name="Default" color="#374151" />
              <Swatch name="Subtle" color="#1f2937" />
              <Swatch name="Hover" color="#4b5563" />
            </div>
          </SubSection>

          <SubSection title="Text">
            <div className="flex flex-wrap gap-4">
              <Swatch name="Primary" color="#f3f4f6" />
              <Swatch name="Secondary" color="#e5e7eb" />
              <Swatch name="Tertiary" color="#d1d5db" />
              <Swatch name="Muted" color="#6b7280" />
              <Swatch name="Disabled" color="#4b5563" />
            </div>
          </SubSection>

          <SubSection title="Accent (Amber)">
            <div className="flex flex-wrap gap-4">
              <Swatch name="Default" color="#d97706" />
              <Swatch name="Hover" color="#f59e0b" />
              <Swatch name="Text" color="#fbbf24" />
              <Swatch name="Surface" color="#451a03" />
              <Swatch name="Border" color="#92400e" />
            </div>
          </SubSection>

          <SubSection title="Semantic">
            <div className="flex flex-wrap gap-6">
              <div>
                <p className="text-[10px] text-gray-500 mb-2">Danger</p>
                <div className="flex gap-3">
                  <Swatch name="Surface" color="#450a0a" />
                  <Swatch name="BG" color="#7f1d1d" />
                  <Swatch name="Border" color="#991b1b" />
                  <Swatch name="Text" color="#f87171" />
                </div>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 mb-2">Success</p>
                <div className="flex gap-3">
                  <Swatch name="Surface" color="#052e16" />
                  <Swatch name="Border" color="#065f46" />
                  <Swatch name="Text" color="#34d399" />
                </div>
              </div>
              <div>
                <p className="text-[10px] text-gray-500 mb-2">Info</p>
                <div className="flex gap-3">
                  <Swatch name="Surface" color="#082f49" />
                  <Swatch name="Border" color="#075985" />
                  <Swatch name="Text" color="#38bdf8" />
                </div>
              </div>
            </div>
          </SubSection>

          <SubSection title="Chart Palette">
            <div className="flex flex-wrap gap-4">
              <Swatch name="Gold" color="#c89b3c" />
              <Swatch name="Teal" color="#0397ab" />
              <Swatch name="Red" color="#e44040" />
              <Swatch name="Mint" color="#3bbf9e" />
              <Swatch name="Purple" color="#9d48e0" />
              <Swatch name="Blue" color="#576bce" />
            </div>
          </SubSection>

          <SubSection title="Tier Colors">
            <div className="flex flex-wrap gap-3">
              {TIER_ORDER.map((tier) => (
                <Swatch key={tier} name={tier} color={TIER_COLORS[tier]} />
              ))}
            </div>
          </SubSection>
        </Section>

        {/* ─── Typography ─── */}
        <Section title="Typography">
          <div className="space-y-4">
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">4xl / 36px</span>
              <span className="text-4xl font-bold text-gray-100">페이지 제목</span>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">3xl / 30px</span>
              <span className="text-3xl font-bold text-gray-100">페이지 제목</span>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">2xl / 24px</span>
              <span className="text-2xl font-extrabold text-amber-400">85.2</span>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">xl / 20px</span>
              <span className="text-xl font-bold text-gray-100">섹션 제목</span>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">lg / 18px</span>
              <span className="text-lg font-bold text-gray-100">섹션 제목</span>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">base / 16px</span>
              <span className="text-base font-semibold text-gray-100">본문 텍스트</span>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">sm / 14px</span>
              <span className="text-sm text-gray-300">본문 텍스트, 버튼, 인풋</span>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">xs / 12px</span>
              <span className="text-xs text-gray-400">보조 텍스트, 뱃지, 태그</span>
            </div>
            <div className="flex items-baseline gap-4">
              <span className="text-[10px] text-gray-500 w-16 text-right shrink-0">2xs / 10px</span>
              <span className="text-[10px] text-gray-500">부가 정보, 라인 라벨</span>
            </div>
          </div>

          <div className="mt-8">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Font Weights</h3>
            <div className="space-y-2">
              <p className="text-sm font-normal text-gray-300">Regular (400) — 일반 본문</p>
              <p className="text-sm font-medium text-gray-300">Medium (500) — 라벨, 보조 텍스트</p>
              <p className="text-sm font-semibold text-gray-300">Semibold (600) — 버튼, 강조 값</p>
              <p className="text-sm font-bold text-gray-300">Bold (700) — 제목, 헤더</p>
              <p className="text-sm font-extrabold text-gray-300">Extrabold (800) — 랭크 뱃지, 점수</p>
            </div>
          </div>
        </Section>

        {/* ─── Spacing & Radius ─── */}
        <Section title="Spacing & Border Radius">
          <SubSection title="Spacing Scale">
            <div className="flex items-end gap-3">
              {[
                { label: '1', px: 4 },
                { label: '1.5', px: 6 },
                { label: '2', px: 8 },
                { label: '2.5', px: 10 },
                { label: '3', px: 12 },
                { label: '4', px: 16 },
                { label: '5', px: 20 },
                { label: '6', px: 24 },
                { label: '8', px: 32 },
                { label: '12', px: 48 },
              ].map((s) => (
                <div key={s.label} className="flex flex-col items-center gap-1">
                  <div
                    className="bg-amber-600 rounded-sm"
                    style={{ width: s.px, height: s.px }}
                  />
                  <span className="text-[10px] text-gray-500">{s.label}</span>
                  <span className="text-[10px] text-gray-600">{s.px}px</span>
                </div>
              ))}
            </div>
          </SubSection>

          <SubSection title="Border Radius">
            <div className="flex gap-6">
              {[
                { label: 'sm', class: 'rounded-md', px: '6px' },
                { label: 'md', class: 'rounded-lg', px: '8px' },
                { label: 'lg', class: 'rounded-xl', px: '12px' },
                { label: 'full', class: 'rounded-full', px: '9999px' },
              ].map((r) => (
                <div key={r.label} className="flex flex-col items-center gap-2">
                  <div className={cn('w-16 h-16 bg-gray-800 border border-gray-700', r.class)} />
                  <span className="text-[10px] text-gray-400">{r.label}</span>
                  <span className="text-[10px] text-gray-600">{r.px}</span>
                </div>
              ))}
            </div>
          </SubSection>
        </Section>

        {/* ─── Button ─── */}
        <Section title="Button">
          <SubSection title="Variants">
            <div className="flex flex-wrap items-center gap-3">
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="danger">Danger</Button>
              <Button variant="ghost">Ghost</Button>
            </div>
          </SubSection>

          <SubSection title="Sizes">
            <div className="flex flex-wrap items-center gap-3">
              <Button size="sm">Small</Button>
              <Button size="md">Medium</Button>
              <Button size="lg">Large</Button>
            </div>
          </SubSection>

          <SubSection title="States">
            <div className="flex flex-wrap items-center gap-3">
              <Button>Default</Button>
              <Button disabled>Disabled</Button>
              <Button loading>Loading</Button>
            </div>
          </SubSection>

          <SubSection title="With Icon">
            <div className="flex flex-wrap items-center gap-3">
              <Button variant="secondary" size="md">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                  <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
                </svg>
                뒤로가기
              </Button>
              <Button variant="secondary" size="sm" className="border-dashed">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                  <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
                </svg>
                소환사 추가
              </Button>
            </div>
          </SubSection>

          <SubSection title="Full Width">
            <div className="max-w-md">
              <Button className="w-full" size="lg">조합 분석하기</Button>
            </div>
          </SubSection>
        </Section>

        {/* ─── Card ─── */}
        <Section title="Card">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-xs text-gray-500 mb-2">Default</p>
              <Card>
                <CardContent>
                  <p className="text-sm text-gray-300">카드 기본 컨텐츠 영역입니다.</p>
                </CardContent>
              </Card>
            </div>

            <div>
              <p className="text-xs text-gray-500 mb-2">With Header</p>
              <Card>
                <CardHeader>
                  <h3 className="text-sm font-bold text-gray-100">카드 제목</h3>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-300">카드 내용이 들어가는 영역입니다.</p>
                </CardContent>
              </Card>
            </div>

            <div>
              <p className="text-xs text-gray-500 mb-2">With Accent Border</p>
              <Card className="border-amber-500/40">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-gray-100">추천 조합 #1</h3>
                    <span className="text-2xl font-extrabold text-amber-400">85.2</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-300">최고 추천 조합의 카드 스타일입니다.</p>
                </CardContent>
              </Card>
            </div>

            <div>
              <p className="text-xs text-gray-500 mb-2">With Color Bar</p>
              <Card className="overflow-hidden">
                <div className="h-1 w-full" style={{ background: '#c89b3c' }} />
                <CardContent>
                  <p className="text-sm text-gray-300">상단에 티어 컬러 바가 있는 카드입니다.</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </Section>

        {/* ─── Input ─── */}
        <Section title="Input">
          <div className="max-w-md space-y-6">
            <SubSection title="States">
              <div className="space-y-4">
                <div>
                  <p className="text-[10px] text-gray-500 mb-1">Default</p>
                  <Input
                    placeholder="소환사이름#태그 (예: Hide on bush#KR1)"
                  />
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 mb-1">With Label</p>
                  <Input
                    label="Riot API 키"
                    placeholder="RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  />
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 mb-1">Error</p>
                  <Input
                    placeholder="소환사이름#태그"
                    error="올바른 형식이 아닙니다 (이름#태그)"
                    value="잘못된입력"
                    onChange={() => {}}
                  />
                </div>
                <div>
                  <p className="text-[10px] text-gray-500 mb-1">With Number Prefix</p>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gray-500 font-medium">
                      1.
                    </span>
                    <input
                      type="text"
                      placeholder="소환사이름#태그"
                      className="w-full rounded-lg border bg-gray-900 pl-8 pr-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-600 border-gray-700 focus:outline-none focus:ring-2 focus:ring-amber-500/40"
                    />
                  </div>
                </div>
              </div>
            </SubSection>

            <SubSection title="Textarea">
              <textarea
                placeholder="롤 로비 채팅을 붙여넣거나 쉼표로 구분하여 입력하세요"
                rows={4}
                className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2.5 text-sm text-gray-100 placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-sky-500/40 resize-none"
              />
            </SubSection>

            <SubSection title="Select">
              <select className="rounded-md border bg-gray-900 px-2 py-1.5 text-xs text-gray-300 border-gray-700 focus:ring-1 focus:ring-amber-500/40 focus:outline-none cursor-pointer">
                <option>챔피언 선택...</option>
                <option>Aatrox</option>
                <option>Ahri</option>
                <option>Yasuo</option>
              </select>
            </SubSection>
          </div>
        </Section>

        {/* ─── ProgressBar ─── */}
        <Section title="ProgressBar">
          <div className="max-w-md space-y-6">
            <ProgressBar value={75} label="분석 진행률" />
            <ProgressBar value={42} label="라인 점수" barColor="bg-cyan-500" />
            <ProgressBar value={33} showPercent={false} />
          </div>
        </Section>

        {/* ─── Tags & Badges ─── */}
        <Section title="Tags & Badges">
          <SubSection title="Status Tags">
            <div className="flex flex-wrap gap-2">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800">
                강점 태그
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-950 text-red-300 border border-red-800">
                약점 태그
              </span>
              <span className="text-xs px-3 py-1.5 rounded-lg bg-amber-950 border border-amber-800 font-bold text-amber-400">
                팀파이트 조합
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
                프론트라인
              </span>
              <span className="text-xs px-2.5 py-1 rounded-full bg-red-950 text-red-400 border border-red-800">
                프론트라인 없음
              </span>
            </div>
          </SubSection>

          <SubSection title="Count Badge">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-gray-100">플레이어 정보</span>
              <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">3명</span>
            </div>
          </SubSection>

          <SubSection title="Rank Badges">
            <div className="flex gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center font-extrabold text-lg bg-amber-500 text-gray-900">
                1
              </div>
              <div className="w-9 h-9 rounded-lg flex items-center justify-center font-extrabold text-lg bg-gray-400 text-gray-900">
                2
              </div>
              <div className="w-9 h-9 rounded-lg flex items-center justify-center font-extrabold text-lg bg-amber-700 text-gray-100">
                3
              </div>
            </div>
          </SubSection>

          <SubSection title="Toggle Buttons (Match Count)">
            <div className="flex gap-2 max-w-xs">
              {[10, 15, 20].map((count, i) => (
                <button
                  key={count}
                  className={cn(
                    'flex-1 py-2 rounded-lg text-sm font-semibold transition-colors border cursor-pointer',
                    i === 0
                      ? 'bg-amber-950 border-amber-700 text-amber-400'
                      : 'bg-gray-800 border-gray-700 text-gray-400'
                  )}
                >
                  {count}판
                </button>
              ))}
            </div>
          </SubSection>

          <SubSection title="Multi-search Toggle">
            <div className="flex gap-2">
              <button className="text-[11px] px-2.5 py-1 rounded-full border bg-sky-950 border-sky-800 text-sky-400 cursor-pointer">
                멀티서치 ON
              </button>
              <button className="text-[11px] px-2.5 py-1 rounded-full border bg-gray-800 border-gray-700 text-gray-400 cursor-pointer">
                멀티서치 OFF
              </button>
            </div>
          </SubSection>
        </Section>

        {/* ─── Win Rate Colors ─── */}
        <Section title="Win Rate Colors">
          <div className="flex gap-6">
            <div className="text-center">
              <span className="text-lg font-medium text-emerald-400">67%</span>
              <p className="text-[10px] text-gray-500 mt-1">60%+</p>
            </div>
            <div className="text-center">
              <span className="text-lg font-medium text-amber-400">53%</span>
              <p className="text-[10px] text-gray-500 mt-1">50-59%</p>
            </div>
            <div className="text-center">
              <span className="text-lg font-medium text-red-400">42%</span>
              <p className="text-[10px] text-gray-500 mt-1">50% 미만</p>
            </div>
          </div>
        </Section>

        {/* ─── Champion Components ─── */}
        <Section title="Champion Components">
          <SubSection title="Champion Icon (Sizes)">
            <div className="flex items-end gap-4">
              <div className="text-center">
                <ChampionIcon championName="Aatrox" size={20} showTooltip={false} />
                <p className="text-[10px] text-gray-500 mt-1">20px</p>
              </div>
              <div className="text-center">
                <ChampionIcon championName="Ahri" size={32} showTooltip={false} />
                <p className="text-[10px] text-gray-500 mt-1">32px</p>
              </div>
              <div className="text-center">
                <ChampionIcon championName="Yasuo" size={40} showTooltip={false} />
                <p className="text-[10px] text-gray-500 mt-1">40px</p>
              </div>
              <div className="text-center">
                <ChampionIcon championName="Jinx" size={48} showTooltip={false} />
                <p className="text-[10px] text-gray-500 mt-1">48px</p>
              </div>
            </div>
          </SubSection>

          <SubSection title="Champion Badge">
            <div className="flex flex-wrap gap-3">
              <ChampionBadge
                championName="Yasuo"
                winRate={0.65}
                kda={3.2}
                games={42}
                size="sm"
              />
              <ChampionBadge
                championName="Ahri"
                winRate={0.52}
                kda={2.8}
                games={28}
                size="md"
              />
              <ChampionBadge
                championName="Jinx"
                winRate={0.45}
                kda={4.1}
                games={15}
                size="lg"
              />
            </div>
          </SubSection>

          <SubSection title="Lane Assignment Slot">
            <div className="flex gap-2">
              {/* Filled */}
              <div className="flex flex-col items-center gap-1.5 p-2 rounded-lg bg-gray-800 border border-gray-700">
                <span className="text-[10px] font-semibold text-amber-500 uppercase tracking-wider">탑</span>
                <ChampionIcon championName="Aatrox" size={40} showTooltip={false} />
                <div className="text-center">
                  <p className="text-[11px] font-semibold text-gray-200">Player1</p>
                  <p className="text-[10px] text-gray-400">Aatrox</p>
                </div>
                <span className="text-[10px] font-medium text-emerald-400">62%</span>
              </div>
              {/* Empty */}
              <div className="flex flex-col items-center gap-1.5 p-2 rounded-lg bg-gray-800/50 border border-gray-700 opacity-40">
                <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">서포터</span>
                <div className="w-10 h-10 rounded-lg bg-gray-700 flex items-center justify-center">
                  <span className="text-gray-600 text-lg">?</span>
                </div>
                <span className="text-[10px] text-gray-600">미배정</span>
              </div>
            </div>
          </SubSection>
        </Section>

        {/* ─── Ban/Pick Slots ─── */}
        <Section title="Ban/Pick Slots">
          <SubSection title="Ban Slot">
            <div className="flex gap-2">
              {/* Banned */}
              <div className="relative aspect-square w-14 rounded-lg flex items-center justify-center border bg-red-950 border-red-800">
                <ChampionIcon championName="Yasuo" size={36} showTooltip={false} className="opacity-60" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-6 h-6 text-red-500/80">
                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                  </svg>
                </div>
              </div>
              {/* Empty */}
              <div className="aspect-square w-14 rounded-lg flex items-center justify-center border bg-gray-800/50 border-gray-700">
                <span className="text-gray-600 text-xs">1</span>
              </div>
            </div>
          </SubSection>

          <SubSection title="Enemy Pick Slot">
            <div className="flex gap-2">
              {/* Picked */}
              <div className="relative aspect-square w-14 rounded-lg flex flex-col items-center justify-center gap-1 border-2 bg-red-950 border-red-800">
                <ChampionIcon championName="Ahri" size={32} showTooltip={false} />
                <span className="text-[9px] text-gray-400">Ahri</span>
              </div>
              {/* Empty */}
              <div className="aspect-square w-14 rounded-lg flex items-center justify-center border-2 border-dashed bg-gray-800/50 border-gray-700">
                <span className="text-gray-600 text-xs">1</span>
              </div>
            </div>
          </SubSection>

          <SubSection title="Ally Lock Row">
            <div className="space-y-2 max-w-md">
              {/* Locked */}
              <div className="flex items-center gap-3 p-2.5 rounded-lg border bg-amber-950 border-amber-800">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-gray-200 truncate">
                    Player1<span className="text-gray-500">#KR1</span>
                  </p>
                </div>
                <div className="flex items-center gap-1.5 bg-amber-900 rounded-md px-2 py-1">
                  <ChampionIcon championName="Jinx" size={20} showTooltip={false} />
                  <span className="text-xs text-amber-300 font-medium">Jinx</span>
                </div>
              </div>
              {/* Unlocked */}
              <div className="flex items-center gap-3 p-2.5 rounded-lg border bg-gray-800/50 border-gray-700">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-gray-200 truncate">
                    Player2<span className="text-gray-500">#KR2</span>
                  </p>
                </div>
                <select className="rounded-md border bg-gray-900 px-2 py-1.5 text-xs text-gray-300 border-gray-700 cursor-pointer">
                  <option>챔피언 선택...</option>
                </select>
              </div>
            </div>
          </SubSection>
        </Section>

        {/* ─── Info Boxes ─── */}
        <Section title="Info Boxes">
          <div className="max-w-md space-y-4">
            <div className="p-4 rounded-lg bg-red-950 border border-red-900 flex items-start gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-sm text-red-300 font-medium">오류 발생</p>
                <p className="text-xs text-red-400 mt-0.5">소환사를 찾을 수 없습니다.</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-sky-950 border border-sky-800">
              <p className="text-[10px] font-semibold text-sky-400 mb-1.5">운영 가이드</p>
              <p className="text-[11px] text-gray-300 leading-relaxed">
                초반에 탑 주도권을 확보하고 중반 이후 팀파이트를 유도하세요.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-amber-950 border border-amber-800">
              <p className="text-[11px] text-amber-400">
                API 키는 "RGAPI-"로 시작해야 합니다. Dev 키는 24시간마다 갱신이 필요합니다.
              </p>
            </div>
          </div>
        </Section>

        {/* ─── Loading State ─── */}
        <Section title="Loading State">
          <div className="max-w-md">
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-6">
              <div className="text-center mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-800 mb-3">
                  <svg className="animate-spin h-6 w-6 text-amber-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                </div>
                <h3 className="text-base font-bold text-gray-100 mb-1">분석 진행 중</h3>
                <p className="text-xs text-gray-400">Riot API에서 데이터를 수집하고 있습니다</p>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-amber-950 border border-amber-800">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-amber-900 text-amber-400">1</div>
                  <span className="text-xs font-medium text-amber-300">플레이어 정보 조회 중...</span>
                </div>
                <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gray-800/50 border border-transparent">
                  <div className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-gray-800 text-gray-600">2</div>
                  <span className="text-xs font-medium text-gray-600">전적 분석 중...</span>
                </div>
              </div>

              <ProgressBar value={33} showPercent={false} barColor="bg-amber-500" />
            </div>
          </div>
        </Section>

        {/* ─── Tier Badge Preview ─── */}
        <Section title="Tier Indicators">
          <div className="flex flex-wrap gap-3">
            {TIER_ORDER.map((tier) => (
              <div key={tier} className="flex items-center gap-2">
                <div className="h-1 w-8 rounded-full" style={{ background: TIER_COLORS[tier] }} />
                <span className="text-xs font-semibold" style={{ color: TIER_COLORS[tier] }}>
                  {tier}
                </span>
              </div>
            ))}
          </div>
        </Section>

        {/* Footer */}
        <footer className="mt-16 pt-8 border-t border-gray-800 text-center">
          <p className="text-xs text-gray-600">
            Font: Inter &middot; Dark theme only &middot; Tailwind CSS v4
          </p>
        </footer>
      </div>
    </div>
  );
}
