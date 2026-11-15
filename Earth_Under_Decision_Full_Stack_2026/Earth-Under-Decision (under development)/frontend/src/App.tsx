import { useEffect, useMemo, useRef, useState, createContext, useContext, type ReactNode } from 'react';
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import maplibregl from 'maplibre-gl';
import { ResponsiveContainer, LineChart as RechartsLineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, BarChart as RechartsBarChart, Bar } from 'recharts';
import { apiGet, apiPost, API_BASE_URL, type DashboardSummary, type TrendResponse, type MapLayer, type StorySummary, type StoryMonthlyResponse, type PrecipitationGrid } from './lib/api';
import {
  Activity, ArrowLeft, ArrowUpRight, Check, ChevronDown, ChevronLeft, CircleHelp, CloudRain,
  BarChart3, Compass, Database, ExternalLink, Eye, FileText, Filter, Globe2, Layers3, Leaf, LineChart,
  Map as MapIcon, Menu, ShieldCheck, SlidersHorizontal, Thermometer, X, Zap,
} from 'lucide-react';

type Lang = 'ar' | 'en';
type LangContextType = { lang: Lang; setLang: (language: Lang) => void };
const LangContext = createContext<LangContextType>({ lang: 'ar', setLang: () => undefined });
const useLang = () => useContext(LangContext);

const messages: Record<Lang, any> = {
  ar: {
    brand: 'Earth Under Decision', tagline: 'افهم الأرض.. وادعم قرارات أفضل.',
    nav: { home: 'الرئيسية', explore: 'استكشف الأرض', methodology: 'المنهجية', about: 'عن المشروع', platform: 'استكشف المنصة', dashboard: 'لوحة المعلومات', map: 'الخريطة التفاعلية', trends: 'تحليل الاتجاهات', scenario: 'تحليل افتراضي', sources: 'المنهجية ومصادر البيانات' },
    language: 'English', back: 'العودة للرئيسية',
    home: {
      eyebrow: 'تحليل بيئي قائم على رصد الأرض', title: 'الأرض تتغير.. هل نقرأ التغيير بشكل صحيح؟',
      body: 'استكشف التغيرات البيئية من خلال بيانات الأقمار الصناعية، وافهم الاتجاهات والعلاقات المكانية لدعم قرارات أفضل وأكثر وعيًا.',
      primary: 'استكشف المنصة', secondary: 'اكتشف المشروع', imageTag: 'رصد الأرض · دلتا النيل',
      imageCaption: 'صورة مرجعية لدلتا النيل — يلزم تثبيت الإسناد قبل النشر',
      indicatorsTitle: 'ما الذي نراقبه؟', indicatorsDesc: 'ثلاثة مؤشرات بيئية أساسية لبناء قراءة مترابطة للتغيرات.',
      ndviTitle: 'اخضرار الغطاء النباتي', ndviDesc: 'متابعة تغير اخضرار الغطاء النباتي عبر الزمن باستخدام مؤشر NDVI.',
      lstTitle: 'درجة حرارة سطح الأرض', lstDesc: 'رصد حرارة سطح الأرض مع الفصل بين مشاهدات النهار والليل.',
      rainTitle: 'الهطول المطري', rainDesc: 'استكشاف أنماط الهطول والتغيرات الزمنية في كميات الأمطار.',
      learn: 'اعرف المزيد', exploreTitle: 'استكشف الأرض', exploreDesc: 'ابدأ بالسياق العالمي، ثم مصر، وصولًا إلى نطاق الدراسة التجريبي في دلتا النيل.',
      openMap: 'افتح الخريطة التفاعلية', areaTag: 'نطاق دراسة مبدئي',
      processTitle: 'من بيانات الأقمار الصناعية إلى فهم أفضل', processDesc: 'سير عمل واضح من جمع البيانات إلى عرض الأدلة والقيود.',
      step1: 'جمع البيانات', step1d: 'الحصول على بيانات رصد الأرض من مصادر موثوقة.', step2: 'المعالجة والتحليل', step2d: 'تهيئة مجموعات البيانات وفحص التغيرات البيئية.', step3: 'مقارنة المواقع', step3d: 'استكشاف الاختلافات بين المناطق الجغرافية.', step4: 'دعم القرار', step4d: 'عرض النتائج المفهومة مع القيود وعدم اليقين.',
      trustTitle: 'مبني على البيانات.. وموجّه بالأدلة', trustDesc: 'نوضح مصادر البيانات، والمنهجية، والدقة المكانية والزمنية، وجودة البيانات، وعدم اليقين. لا نقدم الاتجاهات التاريخية كتنبؤات مستقبلية.',
      methodology: 'اطّلع على المنهجية', footerDesc: 'منصة لاستكشاف التغيرات البيئية باستخدام بيانات رصد الأرض.', footerNASA: 'مشروع مقدم إلى NASA Space Apps Challenge',
    },
    common: { demo: 'بيانات تجريبية', noData: 'لا توجد مجموعة بيانات موثقة متصلة حتى الآن.', pending: 'قيد التحقق', candidate: 'مصدر مرشح', preliminary: 'نطاق مبدئي', illustrative: 'للتوضيح فقط — ليست نتائج علمية', select: 'اختر', all: 'كل المؤشرات', area: 'منطقة الدراسة', period: 'الفترة الزمنية', indicator: 'المؤشر', viewDetails: 'عرض التفاصيل', source: 'المصدر', resolution: 'الدقة المكانية', frequency: 'الدقة الزمنية', status: 'حالة البيانات', none: 'غير متاح بعد', reset: 'إعادة ضبط', apply: 'تطبيق', close: 'إغلاق', notes: 'ملاحظات', verified: 'موثق', notVerified: 'لم يتم التحقق', day: 'نهاري', night: 'ليلي' },
    workspace: { welcome: 'مرحبًا بك في', subtitle: 'مساحة عمل لاستكشاف مؤشرات رصد الأرض وفهم التغيرات البيئية.', overview: 'نظرة عامة', available: 'حالة المنصة', noVerified: 'لا توجد بيانات موثقة متصلة', quick: 'الوصول السريع', recent: 'آخر التحليلات', emptyRecent: 'ستظهر التحليلات هنا بعد تشغيل معالجة بيانات موثقة.', dataCoverage: 'تغطية البيانات', selected: 'النطاق المحدد', mapPreview: 'نظرة جغرافية', selectedArea: 'دلتا النيل — نطاق تجريبي', dataStatus: 'حالة مصادر البيانات', datasets: 'مجموعات البيانات', connected: 'متصل', disconnected: 'غير متصل', awaiting: 'بانتظار التحقق', overviewTitle: 'لوحة المعلومات الرئيسية', overviewDesc: 'نظرة منظمة على المؤشرات ونطاق الدراسة وحالة البيانات المتاحة.',
      mapTitle: 'استكشف الأرض', mapDesc: 'استكشف النطاق الجغرافي واختر المؤشر والفترة. لا توجد طبقات رصد فعلية متصلة بعد.', layers: 'الطبقات', basemap: 'الخريطة الأساسية', focusAreas: 'مناطق الدراسة المرشحة', noRaster: 'لا توجد طبقة Raster موثقة متصلة', mapDisclaimer: 'الخريطة الأساسية مرجعية فقط؛ لا تمثل قياسات NASA أو طبقة رصد بيئي.', layerUnavailable: 'طبقة المؤشر غير متاحة حتى يتم توصيل بيانات موثقة.',
      trendTitle: 'تحليل الاتجاهات', trendDesc: 'فحص التغيرات الزمنية ومقارنة المناطق عند توافر بيانات موثقة.', trendChart: 'السلسلة الزمنية', trendEmpty: 'سيظهر تحليل الاتجاهات بعد توصيل مجموعات بيانات موثقة والتحقق من جودتها.', methodTitle: 'معلومات التحليل', methodBody: 'لن يتم عرض معدل تغير أو دلالة إحصائية قبل تنفيذ اختبار صحيح على بيانات فعلية.', comparison: 'مقارنة المناطق', quality: 'جودة البيانات وعدم اليقين',
      scenarioTitle: 'تحليل افتراضي', scenarioDesc: 'واجهة لاستكشاف الافتراضات. لا يوجد نموذج تنبؤ موثق متصل حاليًا.', scenarioLabel: 'معاينة سيناريو — للتوضيح فقط', assumption: 'افتراض تجريبي', baseline: 'خط الأساس', scenario: 'السيناريو', scenarioNotice: 'لن تعرض هذه الصفحة توقعًا أو نتيجة مستقبلية. سيتم تفعيل الحسابات فقط عند اعتماد نموذج موثق ومدخلات واضحة.', parameter: 'تعديل الافتراض', parameterDesc: 'غيّر قيمة افتراضية لمعاينة طريقة إعداد السيناريو، دون احتساب أثر بيئي.', assumptionValue: 'قيمة افتراضية', noModel: 'لا يوجد نموذج حسابي متصل', saveScenario: 'حفظ إعداد السيناريو محليًا', saved: 'تم حفظ الإعداد محليًا في هذه الجلسة فقط',
      methodologyTitle: 'المنهجية ومصادر البيانات', methodologyDesc: 'تعريف بالمؤشرات المرشحة ومعلومات الدقة والمنهجية والقيود العلمية.', workflow: 'سير عمل البيانات', dataSources: 'مصادر البيانات الأساسية', limitations: 'التعريفات والقيود العلمية', acquisition: 'حالة الحصول على البيانات', notDownloaded: 'لم يتم تأكيد التحميل أو الفحص داخل هذه الواجهة.',
      search: 'ابحث في المنصة', filters: 'عوامل التصفية', menu: 'القائمة', collapse: 'طي القائمة', expand: 'فتح القائمة', help: 'مساعدة', selectedIndicator: 'المؤشر المحدد', view: 'عرض',
    },
    areas: { global: 'السياق العالمي', egypt: 'مصر', nile: 'دلتا النيل', gharbia: 'الغربية', kafr: 'كفر الشيخ', sharqia: 'الشرقية' },
    foot: 'Earth Under Decision · Team NON-HUMAN',
  },
  en: {
    brand: 'Earth Under Decision', tagline: 'Understand Earth. Support Better Decisions.',
    nav: { home: 'Home', explore: 'Explore Earth', methodology: 'Methodology', about: 'About', platform: 'Explore Platform', dashboard: 'Main Dashboard', map: 'Explore Map', trends: 'Trend Analysis', scenario: 'What-If Analysis', sources: 'Methodology & Data Sources' },
    language: 'العربية', back: 'Back to home',
    home: {
      eyebrow: 'Satellite-based environmental analysis', title: 'Earth is changing. Are we reading the change correctly?',
      body: 'Explore environmental change through Earth-observation data, understand spatial patterns and trends, and support better-informed decisions.',
      primary: 'Explore Platform', secondary: 'Discover the Project', imageTag: 'Earth Observation · Nile Delta',
      imageCaption: 'Nile Delta visual reference — verify image attribution before publication',
      indicatorsTitle: 'What Are We Monitoring?', indicatorsDesc: 'Three core environmental indicators for a connected view of change.',
      ndviTitle: 'Vegetation Greenness', ndviDesc: 'Track changes in vegetation greenness over time using NDVI.',
      lstTitle: 'Land Surface Temperature', lstDesc: 'Observe land surface temperature, keeping daytime and nighttime observations separate.',
      rainTitle: 'Precipitation', rainDesc: 'Explore precipitation patterns and temporal changes in rainfall.',
      learn: 'Learn more', exploreTitle: 'Explore the Earth', exploreDesc: 'Start with global context, move to Egypt, and then explore the preliminary Nile Delta pilot area.',
      openMap: 'Open Interactive Map', areaTag: 'Preliminary study area',
      processTitle: 'From Satellite Data to Better Understanding', processDesc: 'A transparent workflow from data collection to evidence and limitations.',
      step1: 'Collect Data', step1d: 'Acquire Earth-observation data from trusted sources.', step2: 'Process & Analyze', step2d: 'Prepare datasets and investigate environmental change.', step3: 'Compare Locations', step3d: 'Explore differences between geographic areas.', step4: 'Support Decisions', step4d: 'Present understandable findings with limitations and uncertainty.',
      trustTitle: 'Built on Data. Guided by Evidence.', trustDesc: 'We communicate data sources, methodology, spatial and temporal resolution, data quality, and uncertainty. Historical trends are not presented as future predictions.',
      methodology: 'Explore Methodology', footerDesc: 'A platform for exploring environmental change with Earth-observation data.', footerNASA: 'Submitted to the NASA Space Apps Challenge',
    },
    common: { demo: 'Demo data', noData: 'No verified dataset connected yet.', pending: 'Pending verification', candidate: 'Candidate source', preliminary: 'Preliminary', illustrative: 'Illustrative only — not scientific results', select: 'Select', all: 'All indicators', area: 'Study area', period: 'Date range', indicator: 'Indicator', viewDetails: 'View details', source: 'Source', resolution: 'Spatial resolution', frequency: 'Temporal resolution', status: 'Data status', none: 'Not available yet', reset: 'Reset', apply: 'Apply', close: 'Close', notes: 'Notes', verified: 'Verified', notVerified: 'Not verified', day: 'Daytime', night: 'Nighttime' },
    workspace: { welcome: 'Welcome to', subtitle: 'A workspace for exploring Earth-observation indicators and environmental change.', overview: 'Overview', available: 'Platform status', noVerified: 'No verified data connected', quick: 'Quick access', recent: 'Recent analyses', emptyRecent: 'Analyses will appear here after verified data processing is run.', dataCoverage: 'Data coverage', selected: 'Selected scope', mapPreview: 'Geographic overview', selectedArea: 'Nile Delta — preliminary focus', dataStatus: 'Data source status', datasets: 'Datasets', connected: 'Connected', disconnected: 'Not connected', awaiting: 'Awaiting verification', overviewTitle: 'Main Dashboard', overviewDesc: 'An organized view of indicators, study area, and available data status.',
      mapTitle: 'Explore Earth', mapDesc: 'Explore the geographic scope and choose an indicator and period. No actual observation layers are connected yet.', layers: 'Layers', basemap: 'Basemap', focusAreas: 'Candidate study areas', noRaster: 'No verified raster layer connected', mapDisclaimer: 'The basemap is for geographic reference only; it is not NASA measurements or an environmental observation layer.', layerUnavailable: 'Indicator layer unavailable until verified data is connected.',
      trendTitle: 'Trend Analysis', trendDesc: 'Examine temporal changes and compare locations when verified data is available.', trendChart: 'Time series', trendEmpty: 'Trend analysis will be available once verified datasets are connected and their quality is checked.', methodTitle: 'Analysis notes', methodBody: 'No change rate or statistical significance will be displayed until a valid test is run on real data.', comparison: 'Location comparison', quality: 'Data quality & uncertainty',
      scenarioTitle: 'What-If Analysis', scenarioDesc: 'An interface for exploring assumptions. No verified forecasting model is currently connected.', scenarioLabel: 'Scenario Preview — Illustrative Only', assumption: 'Illustrative assumption', baseline: 'Baseline', scenario: 'Scenario', scenarioNotice: 'This page does not produce a forecast or future result. Calculations will only be enabled when a documented model and clear inputs are available.', parameter: 'Adjust assumption', parameterDesc: 'Change an illustrative input to preview scenario setup, without calculating environmental impact.', assumptionValue: 'Illustrative value', noModel: 'No calculation model connected', saveScenario: 'Save scenario setup locally', saved: 'Setup saved locally for this session only',
      methodologyTitle: 'Methodology & Data Sources', methodologyDesc: 'Candidate indicators, resolution information, methodology, and scientific limitations.', workflow: 'Data workflow', dataSources: 'Core data sources', limitations: 'Definitions & scientific limitations', acquisition: 'Data acquisition status', notDownloaded: 'Download or inspection has not been confirmed in this interface.',
      search: 'Search platform', filters: 'Filters', menu: 'Menu', collapse: 'Collapse menu', expand: 'Open menu', help: 'Help', selectedIndicator: 'Selected indicator', view: 'View',
    },
    areas: { global: 'Global context', egypt: 'Egypt', nile: 'Nile Delta', gharbia: 'Gharbia', kafr: 'Kafr El-Sheikh', sharqia: 'Sharqia' },
    foot: 'Earth Under Decision · Team NON-HUMAN',
  },
};

const dataSources = [
  { id: 'ndvi', short: 'NDVI', title: 'MOD13Q1.061', arTitle: 'مؤشر اخضرار الغطاء النباتي', icon: Leaf, color: 'green', source: 'Terra MODIS', resolution: '250 m', frequency: '16 days', url: 'https://lpdaac.usgs.gov/products/mod13q1v061/', noteAr: 'يمثل اخضرار الغطاء النباتي؛ لا يقيس المحصول أو الري مباشرة.', noteEn: 'Represents vegetation greenness; it does not directly measure crop yield or irrigation.' },
  { id: 'lst', short: 'LST', title: 'MOD11A2.061', arTitle: 'درجة حرارة سطح الأرض', icon: Thermometer, color: 'gold', source: 'Terra MODIS', resolution: '1 km', frequency: '8 days', url: 'https://lpdaac.usgs.gov/products/mod11a2v061/', noteAr: 'درجة حرارة سطح الأرض وليست درجة حرارة الهواء. يجب فصل النهار عن الليل.', noteEn: 'Land surface temperature is not air temperature. Daytime and nighttime must be handled separately.' },
  { id: 'gpm', short: 'GPM', title: 'GPM_3IMERGM v07 Monthly', arTitle: 'الهطول المطري — متوسط زمني لعام 2023', icon: CloudRain, color: 'blue', source: 'NASA GPM / GES DISC', resolution: '0.1°', frequency: 'Monthly product · 2023 time mean', url: 'https://gpm.nasa.gov/data/imerg', noteAr: 'ملف GeoTIFF يضم معدلًا زمنيًا بوحدة مم/ساعة. القيمة السنوية المكافئة مشتقة بضرب المعدل في 24×365 وليست مجموعًا يوميًا أصليًا.', noteEn: 'The supplied GeoTIFF stores a time-mean rate in mm/hr. Annualized equivalents are derived from the rate, not direct daily accumulations.' },
];

function useT() { const { lang } = useLang(); return messages[lang]; }

function Logo({ compact = false }: { compact?: boolean }) {
  const t = useT();
  return <div className={`brand ${compact ? 'brand-compact' : ''}`}>
    <span className="brand-mark"><Globe2 size={25} strokeWidth={1.7} /><i /></span>
    {!compact && <span className="brand-copy"><strong>{t.brand}</strong><small>{t.tagline}</small></span>}
  </div>;
}

function LanguageButton() {
  const { lang, setLang } = useLang();
  const t = useT();
  return <button className="language-button" onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')} aria-label="Switch language">
    <Globe2 size={16} /><span>{t.language}</span>
  </button>;
}

function PublicNav() {
  const t = useT();
  const [menuOpen, setMenuOpen] = useState(false);
  const { lang } = useLang();
  return <header className="public-nav">
    <div className="container nav-inner">
      <Link to="/" className="brand-link"><Logo /></Link>
      <button className="mobile-menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">{menuOpen ? <X /> : <Menu />}</button>
      <nav className={`public-links ${menuOpen ? 'open' : ''}`}>
        <a href="#home" onClick={() => setMenuOpen(false)}>{t.nav.home}</a>
        <a href="#explore" onClick={() => setMenuOpen(false)}>{t.nav.explore}</a>
        <a href="#methodology" onClick={() => setMenuOpen(false)}>{t.nav.methodology}</a>
        <a href="#about" onClick={() => setMenuOpen(false)}>{t.nav.about}</a>
      </nav>
      <div className="nav-actions"><LanguageButton /><Link to="/app" className="button button-gold button-small">{t.nav.platform}<ArrowLeft size={15} className={lang === 'ar' ? '' : 'flip-icon'} /></Link></div>
    </div>
  </header>;
}

function Footer() {
  const t = useT();
  return <footer className="footer">
    <div className="container footer-grid">
      <div><Logo /><p>{t.home.footerDesc}</p><small className="muted">{t.home.footerNASA}</small></div>
      <div className="footer-links"><strong>{t.nav.explore}</strong><Link to="/app">{t.nav.dashboard}</Link><Link to="/app/map">{t.nav.map}</Link><Link to="/app/trends">{t.nav.trends}</Link></div>
      <div className="footer-links"><strong>{t.nav.methodology}</strong><Link to="/app/methodology">{t.nav.sources}</Link><a href="https://www.earthdata.nasa.gov/" target="_blank" rel="noreferrer">NASA Earthdata <ExternalLink size={12}/></a><a href="https://gpm.nasa.gov/data/imerg" target="_blank" rel="noreferrer">NASA GPM <ExternalLink size={12}/></a></div>
    </div>
    <div className="container footer-bottom"><span>{t.foot}</span><span>Earth Imagery × Dark Geospatial</span></div>
  </footer>;
}

function IndicatorVisual({ kind }: { kind: string }) {
  return <div className={`indicator-visual visual-${kind}`} aria-hidden="true">
    <div className="visual-grid" />
    {kind === 'ndvi' && <><span className="ndvi-patch patch-a"/><span className="ndvi-patch patch-b"/><span className="ndvi-patch patch-c"/><span className="visual-caption">NDVI</span></>}
    {kind === 'lst' && <><span className="thermal-ring ring-a"/><span className="thermal-ring ring-b"/><span className="visual-caption">LST</span></>}
    {kind === 'gpm' && <><span className="rain-lines"/><span className="rain-dot dot-a"/><span className="rain-dot dot-b"/><span className="visual-caption">GPM</span></>}
  </div>;
}

function LandingPage() {
  const t = useT();
  const { lang } = useLang();
  const iconSteps = [<Database key="d"/>, <Activity key="a"/>, <MapIcon key="m"/>, <ShieldCheck key="s"/>];
  const steps = [[t.home.step1, t.home.step1d], [t.home.step2, t.home.step2d], [t.home.step3, t.home.step3d], [t.home.step4, t.home.step4d]];
  return <div className="site-shell">
    <PublicNav />
    <main>
      <section id="home" className="hero-section">
        <div className="hero-glow" />
        <div className="container hero-grid">
          <div className="hero-copy">
            <div className="eyebrow"><span className="eyebrow-dot" />{t.home.eyebrow}</div>
            <h1>{t.home.title}</h1>
            <p className="hero-body">{t.home.body}</p>
            <div className="hero-actions"><Link to="/app" className="button button-gold">{t.home.primary}<ArrowLeft size={17} className={lang === 'ar' ? '' : 'flip-icon'}/></Link><a href="#about" className="button button-outline">{t.home.secondary}</a></div>
            <div className="hero-meta"><span><Activity size={14}/>{t.home.eyebrow}</span><span className="meta-separator"/><span>NASA Earth Observation</span></div>
          </div>
          <div className="hero-visual-wrap">
            <div className="hero-frame">
              <img src="https://earthdata.nasa.gov/s3fs-public/imported/Nile_Delta_large.jpg?VersionId=.K.W2dCUH99aKKXOcqSj0NWfD6SmYUty" alt="Nile Delta satellite visual reference; source attribution to be confirmed" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }} />
              <div className="hero-fallback-map" />
              <div className="hero-image-shade" />
              <div className="image-top-label"><span className="live-dot"/>{t.home.imageTag}</div>
              <div className="image-coordinate"><span>30.9° N</span><span>31.1° E</span></div>
              <div className="image-bottom-card"><div className="mini-globe"><Globe2 size={19}/></div><div><strong>{lang === 'ar' ? 'دلتا النيل، مصر' : 'Nile Delta, Egypt'}</strong><small>{t.home.imageCaption}</small></div></div>
            </div>
            <div className="orbit orbit-one"/><div className="orbit orbit-two"/>
            <div className="hero-side-note"><span className="note-line"/>EARTH OBSERVATION / 01</div>
          </div>
        </div>
        <div className="container hero-bottom"><span>01 — 03</span><div className="hero-progress"><i/></div><span>{lang === 'ar' ? 'اكتشف المؤشرات' : 'DISCOVER THE INDICATORS'}</span></div>
      </section>

      <section className="section indicators-section" id="about">
        <div className="container">
          <div className="section-heading"><div><span className="section-kicker">01 / INDICATORS</span><h2>{t.home.indicatorsTitle}</h2><p>{t.home.indicatorsDesc}</p></div><span className="section-number">01</span></div>
          <div className="indicator-grid">
            {dataSources.map((item) => {
              const title = item.id === 'ndvi' ? t.home.ndviTitle : item.id === 'lst' ? t.home.lstTitle : t.home.rainTitle;
              const desc = item.id === 'ndvi' ? t.home.ndviDesc : item.id === 'lst' ? t.home.lstDesc : t.home.rainDesc;
              const Icon = item.icon;
              return <article className="indicator-card" key={item.id}>
                <IndicatorVisual kind={item.id}/>
                <div className="indicator-card-body"><div className="indicator-title-row"><span className={`indicator-icon ${item.color}`}><Icon size={18}/></span><span className="mono-label">{item.short}</span></div><h3>{title}</h3><p>{desc}</p><div className="indicator-card-foot"><span>{item.title}</span><Link to="/app/methodology">{t.home.learn}<ArrowLeft size={14} className={lang === 'ar' ? '' : 'flip-icon'}/></Link></div></div>
              </article>;
            })}
          </div>
        </div>
      </section>

      <section className="section explore-section" id="explore">
        <div className="container explore-grid">
          <div className="explore-visual">
            <div className="map-preview-image"><img src="https://eoimages.gsfc.nasa.gov/images/imagerecords/149000/149183/niledeltaurban_tm5_1984207.jpg" alt="NASA Earth Observatory view of the Nile Delta" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display='none'; }}/><div className="map-preview-overlay"/><div className="map-badge"><MapIcon size={14}/>{t.home.areaTag}</div><div className="map-scan-line"/><div className="map-coord">EGYPT / NILE DELTA</div></div>
            <div className="map-legend"><span><i className="legend-dot green-dot"/>NDVI</span><span><i className="legend-dot gold-dot"/>LST</span><span><i className="legend-dot blue-dot"/>GPM</span></div>
          </div>
          <div className="explore-copy"><span className="section-kicker">02 / GEOSPATIAL</span><h2>{t.home.exploreTitle}</h2><p>{t.home.exploreDesc}</p><div className="area-pills"><span><Globe2 size={14}/> {t.areas.global}</span><ArrowLeft size={14}/><span><MapIcon size={14}/> {t.areas.egypt}</span><ArrowLeft size={14}/><span className="active"><Compass size={14}/> {t.areas.nile}</span></div><Link to="/app/map" className="button button-gold">{t.home.openMap}<ArrowLeft size={17} className={lang === 'ar' ? '' : 'flip-icon'}/></Link><small className="muted-note">{t.home.areaTag}</small></div>
        </div>
      </section>

      <section className="section process-section">
        <div className="container">
          <div className="section-heading"><div><span className="section-kicker">03 / WORKFLOW</span><h2>{t.home.processTitle}</h2><p>{t.home.processDesc}</p></div><span className="section-number">03</span></div>
          <div className="process-grid">{steps.map((step, index) => <div className="process-step" key={step[0]}><div className="process-step-top"><span className="process-icon">{iconSteps[index]}</span><span className="process-index">0{index + 1}</span></div><h3>{step[0]}</h3><p>{step[1]}</p>{index < 3 && <div className="process-connector"/>}</div>)}</div>
        </div>
      </section>

      <section className="section trust-section" id="methodology">
        <div className="container trust-panel"><div className="trust-icon"><ShieldCheck size={30}/></div><div className="trust-copy"><span className="section-kicker">SCIENTIFIC TRANSPARENCY</span><h2>{t.home.trustTitle}</h2><p>{t.home.trustDesc}</p><Link to="/app/methodology" className="text-link">{t.home.methodology}<ArrowLeft size={15} className={lang === 'ar' ? '' : 'flip-icon'}/></Link></div><div className="trust-stats"><div><strong>01</strong><span>{lang === 'ar' ? 'مصادر واضحة' : 'Clear sources'}</span></div><div><strong>02</strong><span>{lang === 'ar' ? 'منهجية شفافة' : 'Transparent methods'}</span></div><div><strong>03</strong><span>{lang === 'ar' ? 'قيود معلنة' : 'Stated limitations'}</span></div></div></div>
      </section>
    </main>
    <Footer />
  </div>;
}

const workspaceNav = [
  { to: '/app', key: 'dashboard', icon: BarChart3, end: true },
  { to: '/app/map', key: 'map', icon: MapIcon },
  { to: '/app/trends', key: 'trends', icon: LineChart },
  { to: '/app/scenario', key: 'scenario', icon: SlidersHorizontal },
  { to: '/app/methodology', key: 'sources', icon: FileText },
];

function WorkspaceLayout({ children }: { children: ReactNode }) {
  const t = useT();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'offline'>('checking');
  const { lang } = useLang();
  const location = useLocation();
  useEffect(() => setSidebarOpen(false), [location.pathname]);
  useEffect(() => {
    const controller = new AbortController();
    apiGet<{status: string}>('/health', controller.signal)
      .then(() => setBackendStatus('connected'))
      .catch(() => { if (!controller.signal.aborted) setBackendStatus('offline'); });
    return () => controller.abort();
  }, []);
  const backendLabel = backendStatus === 'connected'
    ? (lang === 'ar' ? 'واجهة API متاحة' : 'API reachable')
    : backendStatus === 'checking'
      ? (lang === 'ar' ? 'جارٍ فحص API' : 'Checking API')
      : (lang === 'ar' ? 'API غير متاحة' : 'API offline');
  return <div className="workspace-shell">
    <header className="workspace-topbar">
      <div className="workspace-top-left"><Link to="/" className="workspace-brand"><Logo/></Link><span className="workspace-divider"/><span className="workspace-label">{t.nav.platform}</span></div>
      <div className="workspace-top-actions"><span className={`backend-connection ${backendStatus}`} title={API_BASE_URL}><i/>{backendLabel}</span><button className="icon-button mobile-sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Toggle sidebar"><Menu size={19}/></button><LanguageButton/><button className="avatar-button" title="NON-HUMAN">NH</button></div>
    </header>
    <div className="workspace-body">
      <aside className={`workspace-sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-label">{t.workspace.overview}</div>
        <nav className="sidebar-nav">{workspaceNav.map((item) => { const Icon = item.icon; return <NavLink key={item.to} to={item.to} end={item.end} className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}><Icon size={18}/><span>{t.nav[item.key]}</span>{item.key === 'dashboard' && <span className="sidebar-link-dot"/>}</NavLink>; })}</nav>
        <div className="sidebar-bottom"><div className="sidebar-status"><span className="status-dot"/><div><strong>{t.workspace.noVerified}</strong><small>{t.common.pending}</small></div></div><div className="sidebar-project"><div className="project-mini-mark"><Globe2 size={18}/></div><div><strong>NON-HUMAN</strong><small>NASA Space Apps 2026</small></div></div></div>
      </aside>
      {sidebarOpen && <button className="sidebar-scrim" aria-label="Close menu" onClick={() => setSidebarOpen(false)}/>}
      <main className="workspace-main"><div className="workspace-content">{children}<footer className="workspace-footer"><span>{t.foot}</span><span>API-connected preview · verified observations pending</span></footer></div></main>
    </div>
  </div>;
}

function PageHeading({ eyebrow, title, description, actions }: { eyebrow: string; title: string; description: string; actions?: ReactNode }) {
  return <div className="page-heading"><div><div className="page-eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{actions && <div className="page-heading-actions">{actions}</div>}</div>;
}

function StatusPill({ children, tone = 'muted' }: { children: ReactNode; tone?: 'muted' | 'gold' | 'green' | 'blue' }) { return <span className={`status-pill ${tone}`}><i/>{children}</span>; }

function EmptyState({ title, description, icon: Icon = Database }: { title: string; description: string; icon?: any }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={23}/></div><strong>{title}</strong><p>{description}</p></div>;
}

function SelectField({ label, value, onChange, options }: { label: string; value: string; onChange: (v: string) => void; options: {value: string; label: string}[] }) {
  return <label className="filter-field"><span>{label}</span><div className="select-wrap"><select value={value} onChange={(e) => onChange(e.target.value)}>{options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}</select><ChevronDown size={15}/></div></label>;
}

function MetricCard({ icon: Icon, label, value, detail, tone }: { icon: any; label: string; value: string; detail: string; tone: string }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}><Icon size={18}/></div><div className="metric-copy"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div><span className="metric-corner"><ArrowUpRight size={15}/></span></div>;
}

function DashboardPage() {
  const t = useT();
  const { lang } = useLang();
  const [area, setArea] = useState('nile');
  const [period, setPeriod] = useState('2023');
  const [indicator, setIndicator] = useState('all');
  const [backendSummary, setBackendSummary] = useState<DashboardSummary | null>(null);
  const [story, setStory] = useState<StorySummary | null>(null);
  const [monthly, setMonthly] = useState<StoryMonthlyResponse | null>(null);
  const [loadError, setLoadError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      apiGet<DashboardSummary>('/api/v1/dashboard/summary', controller.signal),
      apiGet<StorySummary>('/api/v1/storytelling/summary', controller.signal),
      apiGet<StoryMonthlyResponse>('/api/v1/storytelling/monthly', controller.signal),
    ]).then(([summary, data, series]) => { setBackendSummary(summary); setStory(data); setMonthly(series); })
      .catch(() => { if (!controller.signal.aborted) setLoadError(true); });
    return () => controller.abort();
  }, []);
  const areaOptions = [{value:'nile',label:t.areas.nile}];
  const periodOptions = [{value:'2023',label:'2023'}];
  const indicatorOptions = [{value:'all',label:t.common.all},{value:'precipitation',label:'GPM Precipitation'},{value:'evapotranspiration',label:'GLDAS Evapotranspiration'},{value:'root_moisture',label:'GLDAS Root-zone Moisture'},{value:'ndvi',label:'NDVI'},{value:'lst',label:'LST'}];
  const m = story?.metrics;
  const metricVisible = (key:string) => indicator === 'all' || indicator === key;
  const monthlyRows = (monthly?.series || []).map((r) => ({...r, month_label: new Date(2023, r.month-1, 1).toLocaleString(lang==='ar'?'ar-EG':'en-US',{month:'short'})}));
  return <>
    <PageHeading eyebrow="01 / OVERVIEW" title={t.workspace.overviewTitle} description={t.workspace.overviewDesc} actions={<StatusPill tone={story ? 'green':'gold'}>{story ? (lang==='ar'?'بيانات 2023 متاحة بقيود':'2023 data available with limitations') : t.common.pending}</StatusPill>}/>
    <div className="welcome-strip"><div><span className="welcome-kicker">EARTH OBSERVATION WORKSPACE</span><h2>{t.workspace.welcome} <em>Earth Under Decision</em></h2><p>{lang==='ar'?'بيانات رصد أرض متاحة لعام 2023 — مع توضيح المصدر والنطاق والقيود.':'Available Earth-observation data for 2023, with source, scope, and limitations disclosed.'}</p></div><div className="welcome-orbit"><Globe2 size={56}/><span/></div></div>
    <div className="filter-bar"><div className="filter-bar-title"><Filter size={16}/><strong>{t.workspace.filters}</strong></div><SelectField label={t.common.area} value={area} onChange={setArea} options={areaOptions}/><SelectField label={t.common.period} value={period} onChange={setPeriod} options={periodOptions}/><SelectField label={t.common.indicator} value={indicator} onChange={setIndicator} options={indicatorOptions}/></div>
    <div className="backend-summary-strip"><span className={`backend-summary-dot ${story ? 'available' : 'offline'}`}/><span>{story ? (lang==='ar' ? `فترة البيانات: 2023 · سجلات GLDAS اليومية: ${story.data_inventory.gldas_daily_rows} · خلايا GPM: ${story.data_inventory.gpm_valid_grid_cells} · بيانات NDVI/LST: غير مرفوعة` : `Data period: 2023 · GLDAS daily records: ${story.data_inventory.gldas_daily_rows} · GPM cells: ${story.data_inventory.gpm_valid_grid_cells} · NDVI/LST: not uploaded`) : (loadError ? (lang==='ar'?'تعذر الاتصال بالخادم أو قراءة ملفات البيانات.':'Could not reach the API or read the processed data files.') : (lang==='ar'?'جارٍ تحميل بيانات المشروع…':'Loading project data…'))}</span></div>
    <div className="section-title-row"><div><h2>{lang==='ar'?'المؤشرات المتاحة فعليًا':'Indicators currently available'}</h2><p>{lang==='ar'?'قيم حقيقية من ملفات التنظيف المرفوعة؛ بحذر في تفسيرها.':'Values from the uploaded cleaned datasets, interpreted with limitations.'}</p></div><span className="section-meta">DATA / 2023</span></div>
    <div className="metric-grid">
      {metricVisible('precipitation') && <MetricCard icon={CloudRain} label="GPM_3IMERGM v07" value={m ? `${m.precipitation.value.toFixed(1)} mm/yr*` : '—'} detail={lang==='ar'?'متوسط مكافئ سنوي مشتق من معدل زمني':'Annualized equivalent derived from a time-mean rate'} tone="blue"/>}
      {metricVisible('evapotranspiration') && <MetricCard icon={Activity} label="GLDAS ET · 2023" value={m ? `${m.evapotranspiration.value.toFixed(1)} mm` : '—'} detail={lang==='ar'?'تراكم صافٍ مُنمذج لنقطة شبكة واحدة':'Modelled net accumulation at one grid point'} tone="green"/>}
      {metricVisible('root_moisture') && <MetricCard icon={Layers3} label="GLDAS Root Moisture" value={m ? `${m.root_zone_soil_moisture.value.toFixed(1)} kg/m²` : '—'} detail={lang==='ar'?'متوسط حالة رطوبة الجذور المُنمذجة':'Mean modelled root-zone state'} tone="gold"/>}
      {(indicator==='all' || indicator==='ndvi') && <MetricCard icon={Leaf} label="NDVI" value={lang==='ar'?'غير متاح':'Unavailable'} detail={lang==='ar'?'لم يتم رفع ملفات MOD13Q1':'MOD13Q1 files not uploaded'} tone="green"/>}
      {(indicator==='all' || indicator==='lst') && <MetricCard icon={Thermometer} label="LST" value={lang==='ar'?'غير متاح':'Unavailable'} detail={lang==='ar'?'لم يتم رفع ملفات MOD11A2':'MOD11A2 files not uploaded'} tone="gold"/>}
    </div>
    {m && <div className="science-callout"><ShieldCheck size={18}/><div><strong>{lang==='ar'?'قراءة المؤشرات وحدودها':'Indicator interpretation and limits'}</strong><p>{lang==='ar'?`GPM: ${m.precipitation.calculation} GLDAS: نقطة نموذج واحدة عند 30.9°N, 31.0°E، وليست متوسط الدلتا. لا تمثل قيم التبخر استهلاك الري الفعلي.`:`GPM: ${m.precipitation.calculation} GLDAS describes one model grid point at 30.9°N, 31.0°E, not a Delta-wide average. ET is not actual irrigation consumption.`}</p></div></div>}
    <div className="dashboard-grid storytelling-charts">
      <section className="panel chart-panel"><div className="panel-header"><div><h3>{lang==='ar'?'التبخر-نتح الشهري':'Monthly evapotranspiration'}</h3><p>GLDAS Noah · 2023 · mm/month</p></div><StatusPill tone="green">{lang==='ar'?'بيانات معالجة':'Processed data'}</StatusPill></div>{monthlyRows.length ? <div className="story-chart"><ResponsiveContainer width="100%" height={235}><RechartsBarChart data={monthlyRows}><CartesianGrid strokeDasharray="3 3" stroke="rgba(234,240,244,.10)"/><XAxis dataKey="month_label" stroke="#9BAAB5" tick={{fontSize:11}}/><YAxis stroke="#9BAAB5" tick={{fontSize:11}}/><Tooltip contentStyle={{background:'#102B40',border:'1px solid rgba(234,240,244,.16)',borderRadius:10,color:'#EAF0F4'}}/><Bar dataKey="evapotranspiration_mm" fill="#238B68" radius={[5,5,0,0]}/></RechartsBarChart></ResponsiveContainer></div> : <EmptyState title={lang==='ar'?'لا توجد بيانات شهرية':'No monthly data'} description={t.common.noData}/>}</section>
      <section className="panel chart-panel"><div className="panel-header"><div><h3>{lang==='ar'?'رطوبة منطقة الجذور':'Root-zone soil moisture'}</h3><p>GLDAS Noah · monthly mean · kg m⁻²</p></div><StatusPill tone="gold">{lang==='ar'?'حالة نموذجية':'Modelled state'}</StatusPill></div>{monthlyRows.length ? <div className="story-chart"><ResponsiveContainer width="100%" height={235}><RechartsLineChart data={monthlyRows}><CartesianGrid strokeDasharray="3 3" stroke="rgba(234,240,244,.10)"/><XAxis dataKey="month_label" stroke="#9BAAB5" tick={{fontSize:11}}/><YAxis stroke="#9BAAB5" tick={{fontSize:11}}/><Tooltip contentStyle={{background:'#102B40',border:'1px solid rgba(234,240,244,.16)',borderRadius:10,color:'#EAF0F4'}}/><Line type="monotone" dataKey="root_moisture_mean_kg_m2" stroke="#D9AC38" strokeWidth={2.4} dot={{r:3}}/></RechartsLineChart></ResponsiveContainer></div> : <EmptyState title={t.common.noData} description={t.common.noData}/>}</section>
    </div>
    {m && <div className="science-callout subtle-callout"><CloudRain size={18}/><div><strong>{lang==='ar'?'بيانات المحطة الخارجية':'External station reference'}</strong><p>{lang==='ar'?`NOAA Alexandria: ${m.noaa_temperature_reference.available_days} يومًا بدرجة حرارة متوسطة متاحة حتى ${m.noaa_temperature_reference.last_available_date}. هذه بيانات NOAA وليست NASA.`:`NOAA Alexandria: ${m.noaa_temperature_reference.available_days} mean-temperature days through ${m.noaa_temperature_reference.last_available_date}. This is NOAA data, not NASA.`}</p></div></div>}
    {loadError && <div className="acquisition-notice"><CircleHelp size={18}/><div><strong>{lang==='ar'?'تعذر تحميل بعض البيانات':'Some data could not be loaded'}</strong><p>{lang==='ar'?'تحقق من تشغيل الخادم ووجود ملفات البيانات المعالجة داخل مجلد التخزين.':'Check that the API is running and processed files exist in the configured storage directory.'}</p></div></div>}
    <div className="quick-access"><div className="section-title-row"><div><h2>{t.workspace.quick}</h2><p>{lang === 'ar' ? 'انتقل مباشرة إلى أدوات الاستكشاف والتحليل.' : 'Go directly to exploration and analysis tools.'}</p></div></div><div className="quick-grid"><QuickLink to="/app/map" icon={MapIcon} title={t.nav.map} desc={lang==='ar'?'استكشف شبكة أمطار GPM ونقطة GLDAS.':'Explore GPM grid cells and the GLDAS point.'}/><QuickLink to="/app/trends" icon={LineChart} title={t.nav.trends} desc={lang==='ar'?'راجع النمط الموسمي خلال 2023.':'Review the 2023 seasonal profile.'}/><QuickLink to="/app/methodology" icon={FileText} title={t.nav.sources} desc={lang==='ar'?'راجع مصادر البيانات والقيود.':'Review data sources and limitations.'}/></div></div>
  </>;
}

function QuickLink({ to, icon: Icon, title, desc }: { to: string; icon: any; title: string; desc: string }) { return <Link className="quick-link" to={to}><span className="quick-link-icon"><Icon size={19}/></span><span className="quick-link-copy"><strong>{title}</strong><small>{desc}</small></span><ArrowLeft size={16}/></Link>; }

function ExploreMapPage() {
  const t = useT();
  const { lang } = useLang();
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const gldasMarkerRef = useRef<maplibregl.Marker | null>(null);
  const [indicator, setIndicator] = useState('gpm');
  const [area, setArea] = useState('nile');
  const [grid, setGrid] = useState<PrecipitationGrid | null>(null);
  const [mapLayers, setMapLayers] = useState<MapLayer[]>([]);
  const [mapFailed, setMapFailed] = useState(false);
  const [mapInitialized, setMapInitialized] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [showGldas, setShowGldas] = useState(true);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      apiGet<PrecipitationGrid>('/api/v1/storytelling/precipitation-grid', controller.signal),
      apiGet<{items: MapLayer[]}>('/api/v1/maps/layers?indicator=precipitation', controller.signal),
    ]).then(([g, layers]) => { setGrid(g); setMapLayers(layers.items || []); })
      .catch(() => { if (!controller.signal.aborted) setMapFailed(true); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    try {
      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: { version: 8, sources: { carto: { type: 'raster', tiles: ['https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'], tileSize: 256, attribution: '&copy; OpenStreetMap contributors &copy; CARTO' } }, layers: [{ id: 'carto-dark', type: 'raster', source: 'carto' }] },
        center: [31.0, 30.95], zoom: 6.2, minZoom: 4, maxZoom: 13, attributionControl: { compact: true },
      });
      mapRef.current = map;
      map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
      map.on('load', () => {
        setMapInitialized(true);
        const marker = new maplibregl.Marker({ color: '#D9AC38' }).setLngLat([31.0,30.9]).setPopup(new maplibregl.Popup({offset:20}).setHTML('<strong>GLDAS Noah · 0.25° model grid point</strong><br/>30.9°N, 31.0°E<br/>Single model point; not a governorate average.')).addTo(map);
        gldasMarkerRef.current = marker;
      });
      map.on('error', () => setMapFailed(true));
    } catch { setMapFailed(true); }
    return () => { gldasMarkerRef.current?.remove(); mapRef.current?.remove(); mapRef.current = null; };
  }, []);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapInitialized || !grid || !map.isStyleLoaded()) return;
    const sourceId = 'gpm-annualized-grid';
    const layerId = 'gpm-grid-cell-centres';
    if (map.getLayer(layerId)) map.removeLayer(layerId);
    if (map.getSource(sourceId)) map.removeSource(sourceId);
    map.addSource(sourceId, { type: 'geojson', data: {type:'FeatureCollection',features:grid.features} as any });
    map.addLayer({
      id: layerId, type: 'circle', source: sourceId,
      layout: { visibility: showGrid && indicator==='gpm' ? 'visible' : 'none' },
      paint: {
        'circle-radius': ['interpolate',['linear'],['zoom'],4,2,7,5,10,8],
        'circle-color': ['interpolate',['linear'],['get','annualized_equivalent_mm_year'],25,'#e7f4ff',80,'#5ca4cb',140,'#247eaa',220,'#d9ac38',310,'#e67e45'],
        'circle-opacity': 0.84, 'circle-stroke-color': '#eaf0f4', 'circle-stroke-width': 0.45,
      },
    });
    map.on('click', layerId, (event) => {
      const feature = event.features?.[0]; if (!feature || !event.lngLat) return;
      const props = feature.properties as any;
      new maplibregl.Popup({offset:10}).setLngLat(event.lngLat).setHTML(`<strong>GPM_3IMERGM v07</strong><br/>Annualized equivalent: ${Number(props.annualized_equivalent_mm_year).toFixed(1)} mm/year<br/>Mean rate: ${Number(props.precipitation_mean_rate_mm_hr).toFixed(5)} mm/hr<br/><small>Derived from 2023 time-mean rate</small>`).addTo(map);
    });
    map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = ''; });
    return () => { if (map.getLayer(layerId)) map.removeLayer(layerId); if (map.getSource(sourceId)) map.removeSource(sourceId); };
  }, [grid,mapInitialized,showGrid,indicator]);
  useEffect(() => { if (gldasMarkerRef.current) { if (showGldas) gldasMarkerRef.current.addTo(mapRef.current!); else gldasMarkerRef.current.remove(); } }, [showGldas,mapInitialized]);
  useEffect(() => {
    const centers: Record<string,[number,number,number]> = { global:[30,20,2], egypt:[30.8,26.8,5], nile:[31.0,30.95,6.2] };
    const target = centers[area] || centers.nile;
    mapRef.current?.flyTo({center:[target[0],target[1]],zoom:target[2],duration:750});
  },[area]);
  const areaOptions = [{value:'global',label:t.areas.global},{value:'egypt',label:t.areas.egypt},{value:'nile',label:t.areas.nile}];
  const indicatorOptions = [{value:'gpm',label:'GPM IMERG v07 — Precipitation'},{value:'evapotranspiration',label:'GLDAS — Evapotranspiration point'},{value:'root_moisture',label:'GLDAS — Root-zone moisture point'},{value:'ndvi',label:'NDVI — Not uploaded'},{value:'lst',label:'LST — Not uploaded'}];
  return <>
    <PageHeading eyebrow="02 / GEOSPATIAL EXPLORER" title={t.workspace.mapTitle} description={lang==='ar'?'توزيع مكاني لخلايا GPM (مراكز الخلايا) ونقطة شبكة GLDAS؛ دون ادعاء حدود إدارية.':'Spatial view of GPM grid-cell centres and the GLDAS point; no administrative boundaries are implied.'} actions={<StatusPill tone={grid?'green':'gold'}>{grid ? `${grid.cell_count} ${lang==='ar'?'خلية':'cells'}` : t.common.pending}</StatusPill>}/>
    <div className="map-workspace">
      <section className="map-main-panel">
        <div className="map-panel-top"><div><span className="map-panel-kicker">GEOSPATIAL VIEW / 2023</span><strong>{t.areas.nile}</strong></div><span className="map-layer-status"><i/> {loading ? (lang==='ar'?'جار التحميل':'Loading') : grid ? 'GPM_3IMERGM v07' : (lang==='ar'?'الطبقة غير متاحة':'Layer unavailable')}</span></div>
        <div className="map-canvas-wrap"><div ref={mapContainer} className="map-canvas"/><div className="map-north">N</div>{mapFailed && <div className="map-unavailable">{lang==='ar'?'تعذر تحميل الخرائط أو بياناتها. تحقق من اتصال الخادم والإنترنت.':'Could not load the map or its data. Check API and internet connectivity.'}</div>}<div className="map-watermark">GPM GRID CENTRES / 0.1°</div></div>
        <div className="map-footnote"><span><i className="map-key-dot"/> {lang==='ar'?'خريطة أساس مرجعية':'Reference basemap'}</span><span>{grid?.note || t.workspace.mapDisclaimer}</span></div>
        <div className="map-legend"><span>{lang==='ar'?'قيمة مكافئة (مم/سنة)':'Annualized equivalent (mm/year)'}</span><i className="legend-gradient"/><div><small>25</small><small>80</small><small>140</small><small>220</small><small>310</small></div></div>
      </section>
      <aside className="map-control-panel">
        <div className="panel-header"><div><h3>{t.workspace.layers}</h3><p>{lang==='ar'?'إعدادات عرض الطبقات المتاحة':'Available layer controls'}</p></div><Layers3 size={18}/></div>
        <SelectField label={t.common.area} value={area} onChange={setArea} options={areaOptions}/>
        <div className="control-divider"/><label className="control-label">{t.common.indicator}</label>
        <div className="indicator-choice-list">{indicatorOptions.map((opt) => <button key={opt.value} className={`indicator-choice ${indicator===opt.value?'selected':''}`} onClick={() => setIndicator(opt.value)}><span className={`choice-swatch ${opt.value==='gpm'?'gpm':opt.value==='ndvi'?'ndvi':opt.value==='lst'?'lst':'gpm'}`}/><span>{opt.label}</span>{indicator===opt.value && <Check size={15}/>}</button>)}</div>
        <div className="control-divider"/>
        <label className="toggle-row"><span><strong>{lang==='ar'?'شبكة خلايا GPM':'GPM grid cells'}</strong><small>{grid?`${grid.cell_count} · 0.1°`:t.common.pending}</small></span><input type="checkbox" checked={showGrid} disabled={!grid || indicator!=='gpm'} onChange={(e)=>setShowGrid(e.target.checked)}/><i/></label>
        <label className="toggle-row"><span><strong>{lang==='ar'?'نقطة GLDAS النموذجية':'GLDAS model point'}</strong><small>30.9°N, 31.0°E</small></span><input type="checkbox" checked={showGldas} onChange={(e)=>setShowGldas(e.target.checked)}/><i/></label>
        <div className="map-empty-note"><div className="empty-note-icon"><Eye size={17}/></div><strong>{indicator==='gpm' ? (lang==='ar'?'شبكة GPM المتاحة':'GPM grid available') : indicator==='ndvi'||indicator==='lst' ? (lang==='ar'?'البيانات غير مرفوعة':'Dataset not uploaded') : (lang==='ar'?'قيمة GLDAS لنقطة واحدة':'GLDAS point data')}</strong><p>{indicator==='gpm' ? (lang==='ar'?'النقاط تمثل مراكز خلايا شبكة 0.1°، وليست مضلعات أو حدود محافظات.':'Points mark 0.1° grid-cell centres, not polygons or governorate boundaries.') : (lang==='ar'?'NDVI وLST غير متاحين في ملفات البيانات الحالية.':'NDVI and LST are not present in the current uploaded datasets.')}</p></div>
        <div className="map-control-footer"><span>{t.common.notes}</span><small>{lang==='ar'?'مصدر الخريطة GPM time-mean 2023، والنتيجة مشتقة من المعدل.':'Map values are derived from the GPM 2023 time-mean rate.'}</small></div>
      </aside>
    </div>
  </>;
}

function TrendPage() {
  const t = useT();
  const { lang } = useLang();
  const [variable, setVariable] = useState('evapotranspiration');
  const [monthly, setMonthly] = useState<StoryMonthlyResponse | null>(null);
  const [summary, setSummary] = useState<StorySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([apiGet<StoryMonthlyResponse>('/api/v1/storytelling/monthly',controller.signal),apiGet<StorySummary>('/api/v1/storytelling/summary',controller.signal)])
      .then(([m,s])=>{setMonthly(m);setSummary(s);}).catch(()=>{if(!controller.signal.aborted)setError(true);}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[]);
  const rows=(monthly?.series||[]).map((r)=>({...r,month_label:new Date(2023,r.month-1,1).toLocaleString(lang==='ar'?'ar-EG':'en-US',{month:'short'})}));
  const config:Record<string,{key:string;label:string;units:string;color:string;note:string}>={
    evapotranspiration:{key:'evapotranspiration_mm',label:'GLDAS Evapotranspiration',units:'mm/month',color:'#238B68',note:lang==='ar'?'تراكم شهري مشتق من تدفق نموذج GLDAS عند نقطة واحدة. القيم السالبة اليومية حُفظت ولم تُستبدل بصفر.':'Monthly accumulation derived from GLDAS model flux at one grid point. Negative daily values were retained, not replaced with zero.'},
    root_moisture:{key:'root_moisture_mean_kg_m2',label:'GLDAS Root-zone Soil Moisture',units:'kg m⁻²',color:'#D9AC38',note:lang==='ar'?'متوسط شهري لحالة رطوبة الجذور من نموذج GLDAS عند نقطة واحدة، وليس قياسًا حقليًا.':'Monthly mean of modelled root-zone moisture at one GLDAS grid point; not a field measurement.'},
    noaa_air_temperature:{key:'noaa_alexandria_tavg_c_mean',label:'NOAA Alexandria temperature reference',units:'°C',color:'#7aa9c9',note:lang==='ar'?'مقارنة خارجية من NOAA وليست NASA. التغطية متاحة حتى 9 أغسطس 2023، والقيم المفقودة تظل Null.':'External NOAA reference, not NASA. Coverage ends 9 August 2023; missing values remain null.'},
  };
  const selected=config[variable];
  const chartRows=rows.filter((r)=>r[selected.key as keyof typeof r]!==null && r[selected.key as keyof typeof r]!==undefined);
  const options=[{value:'evapotranspiration',label:'GLDAS · Evapotranspiration'},{value:'root_moisture',label:'GLDAS · Root-zone moisture'},{value:'noaa_air_temperature',label:'NOAA · Air temperature reference'}];
  const metrics=summary?.metrics;
  return <>
    <PageHeading eyebrow="03 / SEASONAL PROFILE" title={lang==='ar'?'النمط الموسمي خلال 2023':'2023 Seasonal Profile'} description={lang==='ar'?'استكشاف التغير داخل سنة واحدة بالاعتماد على البيانات الشهرية المعالجة. هذه ليست دراسة اتجاه مناخي طويل الأمد.':'Explore within-year variation using the processed monthly data. This is not a long-term climate-trend study.'} actions={<StatusPill tone="green">2023 · 12 months</StatusPill>}/>
    <div className="filter-bar trend-filter"><div className="filter-bar-title"><SlidersHorizontal size={16}/><strong>{t.workspace.filters}</strong></div><SelectField label={t.common.indicator} value={variable} onChange={setVariable} options={options}/><div className="filter-field"><span>{lang==='ar'?'الفترة':'Period'}</span><strong className="fixed-filter-value">2023-01 → 2023-12</strong></div></div>
    <div className="analysis-overview-grid">
      <div className="panel analysis-primary"><div className="panel-header"><div><h3>{lang==='ar'?'السلسلة الشهرية':'Monthly series'}</h3><p>{selected.label} · {selected.units}</p></div><span className="chart-chip">{chartRows.length} / 12</span></div>
        {loading ? <div className="chart-empty-shell"><div className="chart-empty-center"><strong>{lang==='ar'?'جارٍ تحميل بيانات 2023…':'Loading 2023 observations…'}</strong></div></div> : error ? <EmptyState title={lang==='ar'?'تعذر تحميل البيانات':'Data unavailable'} description={lang==='ar'?'تحقق من API ومجلد data/processed.':'Check API connectivity and data/processed.'}/> : chartRows.length ? <div className="api-chart-wrap"><ResponsiveContainer width="100%" height={290}><RechartsLineChart data={chartRows} margin={{top:12,right:18,bottom:8,left:0}}><CartesianGrid strokeDasharray="3 3" stroke="rgba(234,240,244,.10)"/><XAxis dataKey="month_label" stroke="#9BAAB5" tick={{fontSize:11}}/><YAxis stroke="#9BAAB5" tick={{fontSize:11}}/><Tooltip contentStyle={{background:'#102B40',border:'1px solid rgba(234,240,244,.16)',borderRadius:10,color:'#EAF0F4'}}/><Line type="monotone" dataKey={selected.key} name={selected.label} stroke={selected.color} strokeWidth={2.6} dot={{r:3}} connectNulls={false}/></RechartsLineChart></ResponsiveContainer></div> : <EmptyState title={lang==='ar'?'لا توجد مشاهدات لهذه السلسلة':'No observations for this series'} description={lang==='ar'?'قد تكون هذه الفترة غير متاحة في المصدر.':'The selected period may be unavailable in the source.'} />}
        <div className="chart-legend"><span><i className="legend-dot green-dot"/>{selected.label}</span><span className="muted">{lang==='ar'?'ملخص شهري 2023':'2023 monthly summary'}</span></div>
      </div>
      <div className="analysis-side-stack"><section className="panel"><div className="panel-header"><div><h3>{lang==='ar'?'تفسير المصدر':'Source interpretation'}</h3><p>{lang==='ar'?'التغطية والمنهج':'Coverage & method'}</p></div><ShieldCheck size={18}/></div><p className="panel-description">{selected.note}</p><div className="analysis-note-list"><div><Check size={14}/><span>{lang==='ar'?'البيانات الشهرية مشتقة من ملف التنظيف':'Monthly values read from the cleaned dataset'}</span></div><div><Check size={14}/><span>{lang==='ar'?'لا توجد دلالة إحصائية محسوبة':'No statistical significance calculated'}</span></div><div><Check size={14}/><span>{lang==='ar'?'لا يوجد تنبؤ مستقبلي':'No future forecast'}</span></div></div></section>
        <section className="panel comparison-panel"><div className="panel-header"><div><h3>{lang==='ar'?'أرقام مرجعية':'Reference values'}</h3><p>{lang==='ar'?'المؤشرات الملخصة للعام':'Year-level summary'}</p></div><Activity size={17}/></div>{metrics ? <div className="reference-metrics"><div><span>GLDAS ET</span><strong>{metrics.evapotranspiration.value.toFixed(1)} mm</strong></div><div><span>Root moisture</span><strong>{metrics.root_zone_soil_moisture.value.toFixed(1)} kg/m²</strong></div><div><span>GPM grid mean*</span><strong>{metrics.precipitation.value.toFixed(1)} mm/year</strong></div></div> : <EmptyState title={t.common.noData} description={t.common.noData}/>}</section></div>
    </div>
    <div className="science-callout"><ShieldCheck size={18}/><div><strong>{lang==='ar'?'حدود الاستنتاج':'Inference limits'}</strong><p>{lang==='ar'?'سنة واحدة تسمح بوصف النمط الموسمي فقط. لا نحسب ميلًا طويل الأمد أو Mann–Kendall أو دلالة إحصائية، ولا نستخدم البيانات لتنبؤ مستقبلي.':'One year supports seasonal description only. No long-term slope, Mann–Kendall test, statistical significance, or future forecast is inferred.'}</p></div></div>
  </>;
}

function ScenarioPage() {
  const t = useT();
  const { lang } = useLang();
  const [indicator, setIndicator] = useState('ndvi');
  const [area, setArea] = useState('nile');
  const [assumption, setAssumption] = useState(35);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(false);
  const [savedScenarioId, setSavedScenarioId] = useState<string | null>(null);
  const indicatorOptions = [{value:'ndvi',label:'NDVI'},{value:'lst',label:'LST'},{value:'gpm',label:'GPM'}];
  const areaOptions = Object.entries(t.areas as Record<string, string>).map(([value, label]) => ({ value, label }));
  const saveScenario = async () => {
    setSaving(true); setSaved(false); setSaveError(false); setSavedScenarioId(null);
    const areaIds: Record<string, string> = { global: 'area-global', egypt: 'area-egypt', nile: 'area-nile-delta', gharbia: 'area-gharbia', kafr: 'area-kafr-el-sheikh', sharqia: 'area-sharqia' };
    try {
      const result = await apiPost<{id: string}>('/api/v1/scenarios', { title: `UI scenario ${new Date().toISOString()}`, indicator: indicator === 'gpm' ? 'precipitation' : indicator, study_area_id: areaIds[area] || null, assumptions: { illustrative_parameter_percent: assumption }, baseline_reference: 'User-defined illustrative setup' });
      setSavedScenarioId(result.id); setSaved(true);
    } catch { setSaveError(true); }
    finally { setSaving(false); }
  };
  return <>
    <PageHeading eyebrow="04 / SCENARIO WORKSPACE" title={t.workspace.scenarioTitle} description={t.workspace.scenarioDesc} actions={<StatusPill tone="gold">{t.workspace.scenarioLabel}</StatusPill>}/>
    <div className="scenario-warning"><div className="warning-icon"><CircleHelp size={20}/></div><div><strong>{t.workspace.scenarioLabel}</strong><p>{t.workspace.scenarioNotice}</p></div></div>
    <div className="scenario-grid">
      <section className="panel scenario-controls"><div className="panel-header"><div><h3>{lang==='ar'?'إعداد السيناريو':'Scenario setup'}</h3><p>{t.workspace.parameterDesc}</p></div><SlidersHorizontal size={18}/></div>
        <SelectField label={t.common.area} value={area} onChange={(v)=>{setArea(v);setSaved(false);}} options={areaOptions}/>
        <SelectField label={t.common.indicator} value={indicator} onChange={(v)=>{setIndicator(v);setSaved(false);}} options={indicatorOptions}/>
        <div className="scenario-slider-head"><div><strong>{t.workspace.parameter}</strong><small>{t.workspace.assumption}</small></div><span className="slider-value">{assumption}%</span></div>
        <input className="scenario-slider" type="range" min="0" max="100" value={assumption} onChange={(e)=>{setAssumption(Number(e.target.value));setSaved(false);}}/>
        <div className="slider-scale"><span>0%</span><span>100%</span></div>
        <div className="assumption-input"><label>{t.workspace.assumptionValue}</label><span>{assumption}%</span></div>
        <button className="button button-gold full-width" onClick={saveScenario} disabled={saving}>{saving ? (lang==='ar'?'جارٍ الحفظ…':'Saving…') : t.workspace.saveScenario}<ArrowLeft size={15} className={lang==='ar'?'':'flip-icon'}/></button>
        {saved && <div className="saved-message"><Check size={15}/>{lang==='ar'?'تم حفظ الافتراضات في الخادم دون إجراء تنبؤ.':'Assumptions stored by the backend; no forecast was calculated.'}{savedScenarioId ? ` · ${savedScenarioId.slice(0,8)}` : ''}</div>}
        {saveError && <div className="api-save-error">{lang==='ar'?'تعذر حفظ السيناريو في الخادم. تأكد من تشغيل Backend.':'Could not save the scenario to the backend. Check that the API is running.'}</div>}
      </section>
      <section className="panel scenario-preview"><div className="panel-header"><div><h3>{lang==='ar'?'معاينة المقارنة':'Comparison preview'}</h3><p>{t.common.illustrative}</p></div><span className="scenario-preview-icon"><Activity size={18}/></span></div>
        <div className="scenario-compare"><div className="compare-column"><span>{t.workspace.baseline}</span><div className="compare-placeholder"><div className="compare-lines"><i/><i/><i/></div><span>—</span></div></div><div className="compare-divider"><ArrowLeft size={16}/></div><div className="compare-column"><span>{t.workspace.scenario}</span><div className="compare-placeholder compare-alt"><div className="compare-lines"><i/><i/><i/></div><span>—</span></div></div></div>
        <div className="model-unavailable"><div><Zap size={17}/></div><strong>{t.workspace.noModel}</strong><p>{t.workspace.scenarioNotice}</p></div>
      </section>
    </div>
  </>;
}

function MethodologyPage() {
  const t = useT();
  const { lang } = useLang();
  const [catalog, setCatalog] = useState<any[]>([]);
  const [catalogCount, setCatalogCount] = useState<number | null>(null);
  const [story, setStory] = useState<StorySummary | null>(null);
  const [error,setError]=useState(false);
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([apiGet<{items:any[];count:number}>('/api/v1/storytelling/catalog',controller.signal),apiGet<StorySummary>('/api/v1/storytelling/summary',controller.signal)])
      .then(([c,d])=>{setCatalog(c.items||[]);setCatalogCount(c.count);setStory(d);}).catch(()=>{if(!controller.signal.aborted)setError(true);});
    return () => controller.abort();
  }, []);
  const workflow = lang==='ar' ? ['الحصول على ملفات المصدر','حفظ النسخ الخام دون تعديل','فحص البيانات الوصفية والجودة','إعادة إنتاج خطوات التنظيف','اشتقاق الملخصات والطبقات','عرض النتائج مع القيود'] : ['Acquire source files','Preserve immutable raw copies','Inspect metadata and quality','Reproduce cleaning steps','Derive summaries and layers','Present findings with limitations'];
  const limitations = lang==='ar' ? [
    ['GLDAS','سلسلة النقطة الواحدة عند 30.9°N, 31.0°E ليست متوسطًا مكانيًا للدلتا. التبخر-نتح نموذج طبيعي دون تمثيل استهلاك الري الزراعي الفعلي.'],
    ['GPM','الملف GPM_3IMERGM v07 شهري، لكنه ملف متوسط زمني لمعدل mm/hr لعام 2023. قيمة mm/year المعروضة مكافئ مشتق وليست تجميعًا يوميًا مباشرًا.'],
    ['NOAA','بيانات درجة الحرارة خارج NASA؛ تستخدم للمقارنة فقط، ومحطة الإسكندرية تغطيتها حتى 9 أغسطس 2023.'],
    ['NDVI / LST','ملفات MOD13Q1 وMOD11A2 غير موجودة ضمن الملفات المستلمة، لذلك لا تظهر نتائج لهما.'],
    ['Temporal scope','سنة 2023 تصف الموسمية داخل العام ولا تكفي وحدها لاستنتاج اتجاه مناخي طويل الأمد.'],
    ['Geography','لم يتم تسليم حدود إدارية موثقة؛ نقاط الخريطة مراكز خلايا وليست حدود محافظات.'],
  ] : [
    ['GLDAS','The single point at 30.9°N, 31.0°E is not a Delta-wide spatial mean. ET represents modelled natural response, not actual irrigation-driven agricultural consumption.'],
    ['GPM','The supplied GPM_3IMERGM v07 is a monthly product represented by a 2023 time-mean rate in mm/hr. Displayed mm/year is a derived equivalent, not a direct daily sum.'],
    ['NOAA','Temperature data is external to NASA and used for comparison only; Alexandria station coverage ends on 9 August 2023.'],
    ['NDVI / LST','MOD13Q1 and MOD11A2 files were not included in this upload, so no results are shown for them.'],
    ['Temporal scope','2023 supports within-year seasonality, not inference of a long-term climate trend.'],
    ['Geography','No validated administrative boundaries were supplied; map points are grid-cell centres, not governorate boundaries.'],
  ];
  const statusLabel=(status:string)=>status==='not_uploaded'?(lang==='ar'?'لم يُرفع':'Not uploaded'):status.includes('external')?(lang==='ar'?'مصدر خارجي للمقارنة':'External reference'):status.includes('pending')?(lang==='ar'?'فحص علمي مطلوب':'Scientific review pending'):(lang==='ar'?'ملف مرفوع ومعاين':'Uploaded & inspected');
  return <>
    <PageHeading eyebrow="05 / SCIENTIFIC FOUNDATION" title={t.workspace.methodologyTitle} description={lang==='ar'?'مصادر البيانات الفعلية التي وصلت، وخطوات التنظيف، وحالة كل منتج وحدود الاستنتاج.':'Actual uploaded data sources, cleaning workflow, product status, and inference limits.'} actions={<StatusPill tone={catalogCount ? 'green':'gold'}>{catalogCount ?? '—'} {lang==='ar'?'سجلات':'records'}</StatusPill>}/>
    <section className="panel workflow-panel"><div className="panel-header"><div><h3>{t.workspace.workflow}</h3><p>{lang==='ar'?'المسار الفعلي المستخدم مع الملفات المستلمة.':'Workflow applied to the received files.'}</p></div><Activity size={18}/></div><div className="workflow-steps">{workflow.map((step,index)=><div className="workflow-step" key={step}><span>{String(index+1).padStart(2,'0')}</span><strong>{step}</strong>{index<workflow.length-1 && <ChevronLeft size={15}/>}</div>)}</div></section>
    {story && <div className="backend-summary-strip"><span className="backend-summary-dot available"/><span>{lang==='ar'?`سجلات يومية GLDAS: ${story.data_inventory.gldas_daily_rows} · خلايا GPM: ${story.data_inventory.gpm_valid_grid_cells} · محطات NOAA: ${story.data_inventory.noaa_station_count} · NDVI/LST غير متاحين`:`GLDAS daily rows: ${story.data_inventory.gldas_daily_rows} · GPM cells: ${story.data_inventory.gpm_valid_grid_cells} · NOAA stations: ${story.data_inventory.noaa_station_count} · NDVI/LST unavailable`}</span></div>}
    <div className="section-title-row source-title-row"><div><h2>{t.workspace.dataSources}</h2><p>{lang==='ar'?'حالة مصدر البيانات لا تعني اعتمادًا علميًا نهائيًا.':'Source availability does not imply final scientific validation.'}</p></div><span className="section-meta">LIVE DATA CATALOG</span></div>
    {error && <div className="acquisition-notice"><CircleHelp size={18}/><div><strong>{lang==='ar'?'تعذر تحميل الكتالوج':'Could not load catalog'}</strong><p>{lang==='ar'?'تحقق من اتصال الواجهة بالخادم.':'Check frontend-to-backend connectivity.'}</p></div></div>}
    <div className="source-catalog">{catalog.map((item)=>{const icon=item.indicator==='precipitation'?CloudRain:item.indicator==='evapotranspiration'?Activity:item.indicator==='root_moisture'?Layers3:item.indicator==='air_temperature_reference'?Thermometer:item.indicator==='ndvi'?Leaf:Thermometer;const Icon=icon;return <article className="panel source-card" key={item.id}><div className="source-card-top"><span className={`source-icon ${item.indicator==='precipitation'?'blue':item.indicator==='evapotranspiration'?'green':'gold'}`}><Icon size={19}/></span><StatusPill tone={item.status==='not_uploaded'?'gold':item.status.includes('external')?'blue':'green'}>{statusLabel(item.status)}</StatusPill></div><span className="source-short">{item.product_id} {item.version||''}</span><h3>{item.title}</h3><p className="source-kind">{item.source}</p><div className="source-meta-grid"><div><span>{lang==='ar'?'الفترة':'Period'}</span><strong>{item.period|| (lang==='ar'?'لا توجد ملفات':'No files')}</strong></div><div><span>{t.common.resolution}</span><strong>{item.spatial_resolution||'—'}</strong></div><div><span>{t.common.frequency}</span><strong>{item.temporal_resolution||'—'}</strong></div><div><span>{lang==='ar'?'الوحدات':'Units'}</span><strong>{item.units||'—'}</strong></div></div><div className="source-note">{item.notes}</div><a href={item.source_url} target="_blank" rel="noreferrer" className="source-link">{lang==='ar'?'المصدر':'Source'}<ExternalLink size={13}/></a></article>;})}</div>
    <div className="scientific-limitations"><div className="section-title-row"><div><h2>{t.workspace.limitations}</h2><p>{lang==='ar'?'تظهر هذه القيود في تفسير النتائج والرسوم والخرائط.':'These limitations govern interpretation of all outputs.'}</p></div><ShieldCheck size={20}/></div><div className="limitations-grid">{limitations.map(([title,desc],index)=><div className="limitation-item" key={title}><span>0{index+1}</span><div><strong>{title}</strong><p>{desc}</p></div></div>)}</div></div>
    <div className="acquisition-notice"><Database size={18}/><div><strong>{lang==='ar'?'حالة نطاق المشروع':'Project scope status'}</strong><p>{lang==='ar'?'المتاح حاليًا: GPM وGLDAS. بيانات NOAA للمقارنة فقط. يلزم رفع NDVI وLST واستكمال التحقق العلمي قبل اعتماد نتائج المؤشرات الثلاثة.':'Currently available: GPM and GLDAS. NOAA is comparison-only. NDVI and LST files and scientific review are still required before claiming all three MVP indicators.'}</p></div></div>
  </>;
}

function NotFound() { const t=useT(); return <div className="not-found"><h1>404</h1><p>{t.common.none}</p><Link className="button button-gold" to="/">{t.back}</Link></div>; }

export default function App() {
  const [lang, setLang] = useState<Lang>('ar');
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'; document.body.dir = lang === 'ar' ? 'rtl' : 'ltr'; }, [lang]);
  const contextValue = useMemo(() => ({ lang, setLang }), [lang]);
  return <LangContext.Provider value={contextValue}>
    <Routes>
      <Route path="/" element={<LandingPage/>}/>
      <Route path="/app" element={<WorkspaceLayout><DashboardPage/></WorkspaceLayout>}/>
      <Route path="/app/map" element={<WorkspaceLayout><ExploreMapPage/></WorkspaceLayout>}/>
      <Route path="/app/trends" element={<WorkspaceLayout><TrendPage/></WorkspaceLayout>}/>
      <Route path="/app/scenario" element={<WorkspaceLayout><ScenarioPage/></WorkspaceLayout>}/>
      <Route path="/app/methodology" element={<WorkspaceLayout><MethodologyPage/></WorkspaceLayout>}/>
      <Route path="*" element={<NotFound/>}/>
    </Routes>
  </LangContext.Provider>;
}
