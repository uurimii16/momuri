const API_KEY = 'c914fb43-0d44-4fa7-838a-84619e3486c3';
const GEOCODE_URL = 'https://api.routo.com/v1/geocode';
const POI_SEARCH_URL = 'https://api.routo.com/v1/places/findplacefromtext';
const DIRECTIONS_URL = 'https://api.routo.com/v1/directions/basic';
// 실도로 경로: OSRM(오픈스트리트맵 기반, 무료·무키)
const OSRM_URL = 'https://router.project-osrm.org/route/v1/driving';

const map = new routogl.Map({
  container: 'map',
  style: routogl.RoutoStyle.LIGHT,
  center: [127.5, 35.95],
  zoom: 6.7
});

map.addControl(new routogl.NavigationControl(), 'top-right');
map.addControl(new routogl.ScaleControl(), 'bottom-right');

const detailPanel = document.getElementById('detail-panel');
const detailClose = document.getElementById('detail-close');
const detailBadge = document.getElementById('detail-badge');
const detailKicker = document.getElementById('detail-kicker');
const detailName = document.getElementById('detail-name');
const detailAddress = document.getElementById('detail-address');
const detailDescription = document.getElementById('detail-description');
const detailTypeLabel = document.getElementById('detail-type-label');
const detailType = document.getElementById('detail-type');
const detailCoordsLabel = document.getElementById('detail-coords-label');
const detailCoords = document.getElementById('detail-coords');
const detailMedia = document.querySelector('.detail-media');

const mapModeTabs = Array.from(document.querySelectorAll('[data-map-mode]'));
const languageButtons = Array.from(document.querySelectorAll('[data-language]'));
const translatableElements = Array.from(document.querySelectorAll('[data-i18n]'));
const domesticSections = Array.from(document.querySelectorAll('.domestic-section'));
const hawaiiSections = Array.from(document.querySelectorAll('.hawaii-section'));
const geocodeStatus = document.getElementById('geocode-status');
const courseList = document.getElementById('course-list');
const courseSummary = document.getElementById('course-summary');
const waypointList = document.getElementById('waypoint-list');
const historicSiteStatus = document.getElementById('historic-site-status');
const historicSiteList = document.getElementById('historic-site-list');
const poiSearchForm = document.getElementById('poi-search-form');
const poiSearchInput = document.getElementById('poi-search-input');
const poiSearchMeta = document.getElementById('poi-search-meta');
const poiResults = document.getElementById('poi-results');

const state = {
  courses: [],
  historicSites: [],
  activeMapMode: 'hawaii',
  language: 'ko',
  activeCourseId: null,
  routeMarkers: [],
  historicSiteMarkers: [],
  poiMarker: null,
  activeWaypointId: null,
  activeHistoricSiteId: null,
  routeRequestToken: 0
};

const UI_TEXT = {
  ko: {
    domestic: '문화유산 루트',
    hawaii: '관광쇠퇴 진단',
    intro: '국민여행조사·방문자수·동선 네트워크로 지역 관광쇠퇴를 진단하고, 문화유산 연계 추천 루트로 활성화를 제안하는 데이터 기반 지도입니다.',
    recommendedCourses: '문화유산 추천 루트',
    selectedCourse: '선택한 추천 루트',
    courseEmpty: '루트를 선택하면 문화유산 거점, 방문 순서, 추천 동선이 함께 표시됩니다.',
    creator: '크리에이터',
    courseType: '코스 타입',
    totalDistance: '총 거리',
    totalDuration: '총 소요',
    drive: '이동',
    recommendedStay: '추천 체류',
    routeStatusFallback: '실제 도로 주행 경로를 표시 중입니다.',
    hawaiiSites: '관광 활성화 타깃 (쇠퇴 진단)',
    poiSearch: '지역 검색',
    poiPlaceholder: '예: 창녕, 상주, 괴산',
    searchButton: '검색',
    poiSearchMeta: '복합 관광쇠퇴지수(방문·매력·동선)로 도출한 활성화 우선지역과 문화유산 연계 루트를 보여주는 데이터 기반 지도입니다.',
    searchEmptyInput: '검색어를 입력하세요.',
    searchLoading: (query) => `"${query}" 검색 중`,
    searchResultCount: (query, total, shown) => `"${query}" 검색 결과 ${total}건 중 상위 ${shown}건`,
    searchNoResults: (query) => `"${query}" 검색 결과가 없습니다.`,
    searchError: 'POI 검색 중 오류가 발생했습니다.',
    noSearchResults: '검색 결과가 없습니다.',
    noPhone: '전화번호 없음',
    place: '장소',
    noCategory: '분류 없음',
    detailType: '유형',
    coords: '좌표',
    addressLabel: '주소',
    overlayLabel: '2026 관광데이터 분석',
    overlayTitle: '데이터로 진단하는 지역 관광쇠퇴',
    overlayCopy: '방문 추세·재방문·동선 네트워크 3축으로 쇠퇴를 진단하고, 문화유산 연계 루트로 활성화를 제안합니다.',
    loadingSites: '진단 데이터 불러오는 중',
    siteCount: (count) => `활성화 타깃 ${count}곳`,
    metroSuffix: (count) => ` (+대도시권 ${count})`,
    historicType: '활성화 타깃',
    currentStatus: '진단 유형',
    noAddress: '주소 정보 없음',
    noSites: '표시할 활성화 타깃 데이터가 없습니다.',
    historicalTrace: '복합 관광쇠퇴지수 상위 지역으로, 방문·매력·동선 측면에서 활성화 여지가 큰 곳입니다.',
    genericSignificance: '복합 관광쇠퇴지수 기준 활성화 우선지역입니다.',
    genericStatus: '방문·매력·동선 중 하나 이상에서 쇠퇴가 진단된 지역입니다.',
    photoPending: '사진 추가 예정'
  },
  en: {
    domestic: 'Drive Picks',
    hawaii: 'Heritage Stories',
    intro: 'A new infotainment concept for Kia that connects curated drives and story-led destinations in one continuous journey flow.',
    recommendedCourses: 'Drive Curations',
    selectedCourse: 'Selected Journey Flow',
    courseEmpty: 'Select a drive to view destination context, stay suggestions, and the driving flow together.',
    creator: 'Creator',
    courseType: 'Route Type',
    totalDistance: 'Total Distance',
    totalDuration: 'Total Time',
    drive: 'Drive',
    recommendedStay: 'Recommended Stay',
    routeStatusFallback: 'Showing the real road driving route.',
    hawaiiSites: 'Heritage Story Points',
    poiSearch: 'Destination Discovery',
    poiPlaceholder: 'e.g. Seongsan Ilchulbong, Bugak Skyway',
    searchButton: 'Search',
    poiSearchMeta: 'A concept demo proposing an in-car experience where discovery, understanding, and movement flow naturally together.',
    searchEmptyInput: 'Enter a search term.',
    searchLoading: (query) => `Searching "${query}"`,
    searchResultCount: (query, total, shown) => `Showing top ${shown} of ${total} results for "${query}"`,
    searchNoResults: (query) => `No results for "${query}".`,
    searchError: 'An error occurred while searching POIs.',
    noSearchResults: 'No results.',
    noPhone: 'No phone number',
    place: 'Place',
    noCategory: 'No category',
    detailType: 'Type',
    coords: 'Coordinates',
    addressLabel: 'Address',
    overlayLabel: 'Kia Proposal',
    overlayTitle: 'From Discovery to Drive',
    overlayCopy: 'A next-generation infotainment concept that seamlessly connects discovery, destination context, and decisions to move.',
    loadingSites: 'Loading story points',
    siteCount: (count) => `${count} story points`,
    metroSuffix: (count) => ` (+${count} metro ref.)`,
    historicType: 'Story Point',
    currentStatus: 'Status',
    noAddress: 'No address available',
    noSites: 'No story points to display.',
    historicalTrace: 'This stop lets visitors trace the real places where Korean immigrant life and independence activism in Hawaii took shape.',
    genericSignificance: 'A historic place connected to Korean immigration and independence activism in Hawaii.',
    genericStatus: 'The current condition varies by site; some places have changed use or no longer preserve their original form.',
    photoPending: 'Photo coming soon'
  },
  zh: {
    domestic: '推荐驾驶',
    hawaii: '文化故事',
    intro: '这是为 Kia 提出的全新车载信息娱乐概念，将推荐自驾与故事型目的地探索连接为一条连续体验。',
    recommendedCourses: '推荐驾驶策展',
    selectedCourse: '已选出行流程',
    courseEmpty: '选择驾驶路线后，将同时显示目的地背景、停留建议与整体行驶流程。',
    creator: '创作者',
    courseType: '路线类型',
    totalDistance: '总距离',
    totalDuration: '总用时',
    drive: '行驶',
    recommendedStay: '建议停留',
    routeStatusFallback: '正在显示实际道路行驶路线。',
    hawaiiSites: '文化故事点',
    poiSearch: 'Destination Discovery',
    poiPlaceholder: '例：城山日出峰、北岳Skyway',
    searchButton: '搜索',
    poiSearchMeta: '提出一种让探索、理解与出行自然衔接的车载体验概念演示。',
    searchEmptyInput: '请输入搜索词。',
    searchLoading: (query) => `正在搜索“${query}”`,
    searchResultCount: (query, total, shown) => `“${query}”共有${total}条结果，显示前${shown}条`,
    searchNoResults: (query) => `没有找到“${query}”的搜索结果。`,
    searchError: 'POI 搜索时发生错误。',
    noSearchResults: '没有搜索结果。',
    noPhone: '无电话号码',
    place: '地点',
    noCategory: '无分类',
    detailType: '类型',
    coords: '坐标',
    addressLabel: '地址',
    overlayLabel: 'Kia 提案',
    overlayTitle: '从发现到驾驶',
    overlayCopy: '将内容探索、目的地理解与出行决策自然连接的下一代信息娱乐概念。',
    loadingSites: '正在加载故事点',
    siteCount: (count) => `${count}个故事点`,
    metroSuffix: (count) => `（+大都市圈 ${count}）`,
    historicType: '故事点',
    currentStatus: '状态',
    noAddress: '暂无地址信息',
    noSites: '没有可显示的故事点。',
    historicalTrace: '游客可以在这里沿着真实地点，理解夏威夷韩人移民生活与独立运动留下的痕迹。',
    genericSignificance: '这里是与夏威夷韩人移民史和独立运动相关的历史地点。',
    genericStatus: '各遗址现状不同，部分地点已改变用途或不再保留原貌。',
    photoPending: '照片待添加'
  },
  ja: {
    domestic: 'おすすめドライブ',
    hawaii: 'ヘリテージストーリー',
    intro: 'Kia向けの新しいインフォテインメント構想として、ドライブ提案と物語性のある目的地探索をひとつの流れでつなぎます。',
    recommendedCourses: 'おすすめドライブキュレーション',
    selectedCourse: '選択中のジャーニーフロー',
    courseEmpty: 'ドライブを選ぶと、目的地の文脈、滞在提案、移動フローがまとめて表示されます。',
    creator: 'クリエイター',
    courseType: 'コースタイプ',
    totalDistance: '総距離',
    totalDuration: '総所要時間',
    drive: '移動',
    recommendedStay: 'おすすめ滞在',
    routeStatusFallback: '実際の道路の走行ルートを表示しています。',
    hawaiiSites: 'ヘリテージストーリーポイント',
    poiSearch: 'Destination Discovery',
    poiPlaceholder: '例: 城山日出峰、北岳スカイウェイ',
    searchButton: '検索',
    poiSearchMeta: '探索、理解、移動が自然につながる車内体験を提案するコンセプトデモです。',
    searchEmptyInput: '検索語を入力してください。',
    searchLoading: (query) => `「${query}」を検索中`,
    searchResultCount: (query, total, shown) => `「${query}」の検索結果${total}件のうち上位${shown}件を表示`,
    searchNoResults: (query) => `「${query}」の検索結果はありません。`,
    searchError: 'POI検索中にエラーが発生しました。',
    noSearchResults: '検索結果がありません。',
    noPhone: '電話番号なし',
    place: '場所',
    noCategory: '分類なし',
    detailType: 'タイプ',
    coords: '座標',
    addressLabel: '住所',
    overlayLabel: 'Kia Proposal',
    overlayTitle: 'From Discovery to Drive',
    overlayCopy: 'コンテンツ探索から目的地理解、移動判断まで自然につながる次世代インフォテインメント提案です。',
    loadingSites: 'ストーリーポイントを読み込み中',
    siteCount: (count) => `ストーリーポイント ${count}件`,
    metroSuffix: (count) => `（+大都市圏 ${count}）`,
    historicType: 'ストーリーポイント',
    currentStatus: 'ステータス',
    noAddress: '住所情報なし',
    noSites: '表示できるストーリーポイントがありません。',
    historicalTrace: 'ハワイの韓人移民生活と独立運動の痕跡を、実際の場所をたどりながら感じられる地点です。',
    genericSignificance: 'ハワイの韓人移民史と独立運動に関わる歴史的な場所です。',
    genericStatus: '現在の状態は場所によって異なり、一部は用途が変わったり原形が残っていない場合があります。',
    photoPending: '写真追加予定'
  }
};

const HAWAII_SITE_TRANSLATIONS = {
  'hawaii-historic-1': {
    en: { name: 'Korean Comrade Society Hall, Honolulu (North King Street)', significance: 'A building used as the Korean Comrade Society hall from 1932.', status: 'Now used as commercial space; traces of the 1949 building remain.' },
    zh: { name: '檀香山大韩人同志会馆（北国王街）', significance: '自1932年起作为大韩人同志会会馆使用的建筑。', status: '现为商铺使用，1949年新建建筑的原貌仍有遗存。' },
    ja: { name: 'ホノルル大韓人同志会館（ノース・キング通り）', significance: '1932年から大韓人同志会の会館として使われた建物です。', status: '現在は商業施設として使われ、1949年新築時の姿が一部残っています。' }
  },
  'hawaii-historic-2': {
    en: { name: 'Former Syngman Rhee Residence, Honolulu (Puunui Street)', significance: 'A place where Syngman Rhee lived in Hawaii in 1913.', status: 'Later additions and remodeling make the original traces difficult to see.' },
    zh: { name: '檀香山李承晚旧居遗址（Puunui街）', significance: '1913年李承晚在夏威夷居住过的地点。', status: '经过扩建和改造，过去的痕迹已不易辨认。' },
    ja: { name: 'ホノルル李承晩居住地跡（プウヌイ通り）', significance: '1913年に李承晩がハワイで暮らした場所です。', status: '増改築により、当時の痕跡は見つけにくくなっています。' }
  },
  'hawaii-historic-3': {
    en: { name: 'Korean Christian Church, Honolulu (Liliha Street)', significance: 'A Korean Christian Church building established on Liliha Street in 1938.', status: 'The church building was fully renovated in 2006.' },
    zh: { name: '檀香山韩人基督教会（Liliha街）', significance: '1938年在Liliha街建立的韩人基督教会建筑。', status: '教会建筑于2006年完成全面修缮。' },
    ja: { name: 'ホノルル韓人キリスト教会（リリハ通り）', significance: '1938年にリリハ通りに建てられた韓人キリスト教会の建物です。', status: '2006年に教会建物の全面改修が完了しました。' }
  },
  'hawaii-historic-4': {
    en: { name: 'Korean Christian Church, Honolulu (North School Street)', significance: 'A church founded by followers of Syngman Rhee to support the independence movement.', status: 'Now used as a private home and remodeled as a two-story wooden building.' },
    zh: { name: '檀香山韩人基督教会（North School街）', significance: '追随李承晚的教友为支援独立运动而建立的教会。', status: '现为私人住宅，并改建为两层木结构建筑。' },
    ja: { name: 'ホノルル韓人キリスト教会（ノース・スクール通り）', significance: '李承晩を支持する信徒たちが独立運動を支えるために設立した教会です。', status: '現在は個人住宅として使われ、2階建ての木造建物に改装されています。' }
  },
  'hawaii-historic-5': {
    en: { name: 'St. Luke’s Episcopal Church', significance: 'A Korean Episcopal mission that began in 1905; the current church was dedicated in 1952.', status: 'Currently operating as a church.' },
    zh: { name: '圣路加圣公会教堂', significance: '1905年开始的韩人圣公会传教会，现教堂于1952年奉献。', status: '目前仍作为教堂运营。' },
    ja: { name: '聖ルカ聖公会教会', significance: '1905年に始まった韓人聖公会宣教会で、現在の教会堂は1952年に献堂されました。', status: '現在も教会として運営されています。' }
  },
  'hawaii-historic-6': {
    en: { name: 'Former Shinheung Korean Language School, Honolulu' },
    zh: { name: '檀香山新兴国语学校遗址' },
    ja: { name: 'ホノルル新興国語学校跡' }
  },
  'hawaii-historic-7': {
    en: { name: 'Korean Comrade Society Hall, Honolulu (Kuakini Street)' },
    zh: { name: '檀香山同志会馆（Kuakini街）' },
    ja: { name: 'ホノルル同志会館（クアキニ通り）' }
  },
  'hawaii-historic-8': {
    en: { name: 'Former Korean Association Site, Honolulu' },
    zh: { name: '檀香山韩人协会遗址' },
    ja: { name: 'ホノルル韓人協会跡' }
  },
  'hawaii-historic-9': {
    en: { name: 'Former Nuuanu YMCA Hall Site' },
    zh: { name: 'Nuuanu YMCA会馆遗址' },
    ja: { name: 'ヌウアヌYMCA会館跡' }
  },
  'hawaii-historic-10': {
    en: { name: 'Former Hawaii Branch Office of the Korean Independence League, Honolulu' },
    zh: { name: '檀香山大朝鲜独立团夏威夷支部遗址' },
    ja: { name: 'ホノルル大朝鮮独立団ハワイ支部跡' }
  },
  'hawaii-historic-11': {
    en: { name: 'Oahu Cemetery, Honolulu' },
    zh: { name: '檀香山欧胡公墓' },
    ja: { name: 'ホノルル・オアフ共同墓地' }
  },
  'hawaii-historic-12': {
    en: { name: 'United Korean Association Hall, Honolulu' },
    zh: { name: '檀香山韩人合成协会会馆' },
    ja: { name: 'ホノルル韓人合成協会会館' }
  },
  'hawaii-historic-13': {
    en: { name: 'Former Hanmi-bo Newspaper Site, Honolulu' },
    zh: { name: '檀香山《韩美报》旧址' },
    ja: { name: 'ホノルル『韓米報』跡' }
  },
  'hawaii-historic-14': {
    en: { name: 'Former Korean National Association Headquarters Site (Hawaii Governor’s Residence)' },
    zh: { name: '大韩人国民会总会馆旧址（现夏威夷州长官邸）' },
    ja: { name: '大韓人国民会総会館旧跡（現ハワイ州知事公邸）' }
  },
  'hawaii-historic-15': {
    en: { name: 'Former Korean Boarding School and Korean Methodist Church Site' },
    zh: { name: '韩人寄宿学校与韩人监理教会旧址' },
    ja: { name: '韓人寄宿学校と韓人メソジスト教会旧跡' }
  },
  'hawaii-historic-16': {
    en: { name: 'Hawaii Christ Church (Former Christ United Methodist Church)' },
    zh: { name: '夏威夷基督教会（旧基督联合监理教会）' },
    ja: { name: 'ハワイ・キリスト教会（旧キリスト合同メソジスト教会）' }
  },
  'hawaii-historic-17': {
    en: { name: 'Korean Christian Institute, Honolulu (Kalihi)' },
    zh: { name: '檀香山韩人基督学院（Kalihi）' },
    ja: { name: 'ホノルル韓人基督学院（カリヒ）' }
  },
  'hawaii-historic-18': {
    en: { name: 'Former Ahuimanu Korean Independence Army Training Site' },
    zh: { name: 'Ahuimanu大朝鲜独立军团遗址' },
    ja: { name: 'アフイマヌ大朝鮮独立軍団跡' }
  },
  'hawaii-historic-19': {
    en: { name: 'Former Korean Christian Institute Site, Honolulu (Waialae Avenue)' },
    zh: { name: '檀香山韩人基督学院遗址（Waialae大道）' },
    ja: { name: 'ホノルル韓人基督学院跡（ワイアラエ通り）' }
  },
  'hawaii-historic-20': {
    en: { name: 'Former Korean National Association Hawaii Branch Hall, Honolulu' },
    zh: { name: '檀香山大韩人国民会夏威夷地方会总会馆遗址' },
    ja: { name: 'ホノルル大韓人国民会ハワイ地方会総会館跡' }
  },
  'hawaii-historic-21': {
    en: { name: 'Former Pacific Magazine Publication Site, Honolulu' },
    zh: { name: '檀香山《太平洋杂志》发行地遗址' },
    ja: { name: 'ホノルル『太平洋雑誌』発行地跡' }
  },
  'hawaii-historic-22': {
    en: { name: 'Diamond Head Memorial Park, Honolulu' },
    zh: { name: '檀香山钻石头纪念公园' },
    ja: { name: 'ホノルル・ダイヤモンドヘッド・メモリアルパーク' }
  },
  'hawaii-historic-23': {
    en: { name: 'Former Korean Christian Church Site, Honolulu (Lehua Street)' },
    zh: { name: '檀香山韩人基督教会遗址（Lehua街）' },
    ja: { name: 'ホノルル韓人キリスト教会跡（レフア通り）' }
  },
  'hawaii-historic-24': {
    en: { name: 'Puʻuiki Cemetery' },
    zh: { name: 'Puʻuiki墓地' },
    ja: { name: 'プウイキ墓地' }
  },
  'hawaii-historic-25': {
    en: { name: 'Former Kahuku Korean Independence Army Training Site' },
    zh: { name: 'Kahuku大朝鲜独立军团遗址' },
    ja: { name: 'カフク大朝鮮独立軍団跡' }
  }
};

const COURSE_TRANSLATIONS = {
  'jeju-east': {
    en: {
      title: 'Jeju East Coast Scenic Drive',
      region: 'Eastern Jeju',
      creator: 'Korea Travel Creator Curation',
      theme: 'Coastal Views + Cafes + Photo Spots',
      difficulty: 'Moderate',
      description: 'A relaxed east Jeju coastal drive with sea views, gentle walks, and cafe stops. It is a good way to enjoy open scenery without rushing between places.'
    },
    zh: {
      title: '济州东部海岸风景自驾',
      region: '济州东部',
      creator: '韩国旅行创作者精选',
      theme: '海岸风景 + 咖啡馆 + 拍照点',
      difficulty: '普通',
      description: '这条济州东部海岸路线串联大海、短途散步和咖啡馆停靠点，可以慢慢感受开阔的海边风景。'
    },
    ja: {
      title: '済州東部シーサイドドライブ',
      region: '済州東部',
      creator: '韓国旅行クリエイター選定',
      theme: '海岸風景 + カフェ + フォトスポット',
      difficulty: '普通',
      description: '済州東部の海岸沿いで、海の景色、短い散策、カフェ休憩をゆっくり楽しめるドライブコースです。'
    }
  },
  'seoul-night': {
    en: {
      title: 'Seoul Night View Drive',
      region: 'Seoul',
      creator: 'Urban Drive Editor’s Pick',
      theme: 'Observatories + Night Views + Han River',
      difficulty: 'Easy',
      description: 'A night drive that connects Seoul’s ridgelines, Namsan, and the Han River. It brings together elevated city views and riverside lights in one route.'
    },
    zh: {
      title: '首尔夜景自驾',
      region: '首尔',
      creator: '城市自驾编辑精选',
      theme: '观景点 + 夜景 + 汉江',
      difficulty: '简单',
      description: '这条夜间自驾路线连接首尔山脊、南山和汉江，可以一次感受高处城市夜景与江边灯光。'
    },
    ja: {
      title: 'ソウル夜景ドライブ',
      region: 'ソウル',
      creator: '都市ドライブ編集部セレクション',
      theme: '展望スポット + 夜景 + 漢江',
      difficulty: 'やさしい',
      description: 'ソウルの稜線、南山、漢江の夜景をつなぐドライブコースです。高台の眺めと川沿いの光を一度に楽しめます。'
    }
  }
};

const WAYPOINT_TRANSLATIONS = {
  'jeju-1': {
    en: { name: 'Aqua Planet Jeju', category: 'Experience POI', address: '95 Seopjikoji-ro, Seongsan-eup, Seogwipo-si, Jeju, Korea', description: 'A large aquarium with marine exhibits and indoor viewing spaces. It is a comfortable stop in any weather and a popular place to see Jeju’s sea life up close.' },
    zh: { name: '济州Aqua Planet水族馆', category: '体验型地点', address: '韩国济州特别自治道西归浦市城山邑涉地可支路95', description: '这里有大型水族馆和室内展区，不受天气影响也能停留。可以近距离观察济州海洋生物，家庭游客也很喜欢。' },
    ja: { name: 'アクアプラネット済州', category: '体験型スポット', address: '韓国 済州特別自治道 西帰浦市 城山邑 ソプチコジ路95', description: '大型水族館と屋内展示があり、天気に左右されず過ごせる場所です。済州の海の生き物を近くで見られ、家族連れにも人気があります。' }
  },
  'jeju-2': {
    en: { name: 'Seopjikoji', category: 'Coastal Viewpoint', address: '262 Seopjikoji-ro, Seogwipo-si, Jeju, Korea', description: 'A coastal headland where open grassland meets the blue sea. Its windy hills, lighthouse, and seaside cliffs make it one of east Jeju’s most photogenic places.' },
    zh: { name: '涉地可支', category: '海岸景观点', address: '韩国济州特别自治道西归浦市涉地可支路262', description: '草地与蓝色大海相接的海岸岬角，海风吹过的丘陵、灯塔和海岸悬崖让这里很适合拍照。' },
    ja: { name: 'ソプチコジ', category: '海岸絶景', address: '韓国 済州特別自治道 西帰浦市 ソプチコジ路262', description: '草原と青い海が重なる海岸岬です。風の抜ける丘、灯台、海岸の崖が一緒に見え、済州東部らしい写真を残せます。' }
  },
  'jeju-3': {
    en: { name: 'Seongsan Ilchulbong', category: 'Landmark', address: '284-12 Ilchul-ro, Seogwipo-si, Jeju, Korea', description: 'A volcanic tuff cone rising beside the sea and one of Jeju’s most recognized landscapes. It is especially known for sunrise views and the wide coastal panorama from the crater rim.' },
    zh: { name: '城山日出峰', category: '地标', address: '韩国济州特别自治道西归浦市日出路284-12', description: '耸立在海边的火山凝灰岩山峰，是济州最具代表性的景观之一。这里以日出和从火山口边缘展开的海岸全景而闻名。' },
    ja: { name: '城山日出峰', category: 'ランドマーク', address: '韓国 済州特別自治道 西帰浦市 日出路284-12', description: '海辺にそびえる火山性の峰で、済州を代表する景観の一つです。日の出と火口縁から広がる海岸の眺めで知られています。' }
  },
  'seoul-1': {
    en: { name: 'Bugak Skyway Palgakjeong Pavilion', category: 'Viewpoint', address: '267 Bugaksan-ro, Jongno-gu, Seoul, Korea', description: 'A viewpoint on the Bugaksan ridge overlooking central Seoul. The winding skyway, pavilion, and city lights create a calm nightscape above the city.' },
    zh: { name: '北岳Skyway八角亭', category: '观景点', address: '韩国首尔特别市钟路区北岳山路267', description: '位于北岳山山脊上的观景点，可以俯瞰首尔市中心。蜿蜒的山路、八角亭和城市灯光形成安静的夜景。' },
    ja: { name: '北岳スカイウェイ八角亭', category: '展望ポイント', address: '韓国 ソウル特別市 鍾路区 北岳山路267', description: '北岳山の稜線上にある展望スポットです。曲がりくねったスカイウェイ、八角亭、街の灯りが重なり、落ち着いた夜景を楽しめます。' }
  },
  'seoul-2': {
    en: { name: 'N Seoul Tower Access Point', category: 'Landmark', address: '105 Namsangongwon-gil, Yongsan-gu, Seoul, Korea', description: 'A landmark on Namsan that is instantly associated with Seoul. The tower silhouette, hillside paths, and elevated city lights capture the city’s night atmosphere.' },
    zh: { name: 'N首尔塔入口点', category: '地标', address: '韩国首尔特别市龙山区南山公园路105', description: '位于南山上的首尔代表性地标。塔的剪影、山坡步道和高处城市灯光共同呈现出首尔夜晚的氛围。' },
    ja: { name: 'Nソウルタワーアクセス地点', category: 'ランドマーク', address: '韓国 ソウル特別市 龍山区 南山公園路105', description: '南山に立つソウルを象徴するランドマークです。タワーのシルエット、丘の散策路、高台からの街の灯りがソウルの夜の雰囲気を伝えます。' }
  },
  'seoul-3': {
    en: { name: 'Some Sevit', category: 'Han River Complex POI', address: '2085-14 Olympic-daero, Seocho-gu, Seoul, Korea', description: 'A floating island complex on the Han River. At night, the lights reflect on the water and create a distinctive riverside atmosphere for a walk or a pause by the river.' },
    zh: { name: '三光岛', category: '汉江复合地点', address: '韩国首尔特别市瑞草区奥林匹克大路2085-14', description: '位于汉江上的水上岛屿建筑群。夜晚灯光倒映在水面上，形成独特的江边氛围，适合散步或短暂停留。' },
    ja: { name: 'セビッソム', category: '漢江複合スポット', address: '韓国 ソウル特別市 瑞草区 オリンピック大路2085-14', description: '漢江に浮かぶ人工島の複合施設です。夜は照明が水面に映り、川辺を歩いたり少し立ち止まったりしたくなる独特の雰囲気があります。' }
  }
};

detailClose.addEventListener('click', () => {
  detailPanel.classList.remove('open');
});

mapModeTabs.forEach((button) => {
  button.addEventListener('click', () => {
    setMapMode(button.dataset.mapMode);
  });
});

languageButtons.forEach((button) => {
  button.addEventListener('click', () => {
    setLanguage(button.dataset.language);
  });
});

renderLanguageControls();
renderStaticText();

poiSearchForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const query = poiSearchInput.value.trim();
  if (!query) {
    poiSearchMeta.textContent = getUiText('searchEmptyInput');
    return;
  }

  poiSearchMeta.textContent = getUiText('searchLoading', query);
  poiResults.innerHTML = '';

  try {
    const response = await fetch(`${POI_SEARCH_URL}?input=${encodeURIComponent(query)}&key=${API_KEY}`);
    const data = await response.json();
    const results = Array.isArray(data.result) ? data.result.slice(0, 6) : [];

    poiSearchMeta.textContent = data.total
      ? getUiText('searchResultCount', query, data.total, results.length)
      : getUiText('searchNoResults', query);

    renderPoiResults(results);
  } catch (error) {
    poiSearchMeta.textContent = getUiText('searchError');
  }
});

map.on('load', async () => {
  geocodeStatus.textContent = '루트 데이터 불러오는 중';
  historicSiteStatus.textContent = getUiText('loadingSites');

  try {
    const [courseResponse, historicSiteResponse] = await Promise.all([
      fetch(`data/routes.json?v=${Date.now()}`, { cache: 'no-store' }),
      fetch(`data/targets.json?v=${Date.now()}`, { cache: 'no-store' })
    ]);

    const courses = await courseResponse.json();
    const historicSites = await historicSiteResponse.json();
    state.courses = await Promise.all(courses.map(resolveCourseWaypoints));
    state.historicSites = historicSites.filter(isValidHistoricSite);

    geocodeStatus.textContent = '루트 데이터 준비 완료';
    updateHistoricSiteCount();
    renderCourseList();
    renderHistoricSiteList();
    drawHistoricSites();
    setMapMode(state.historicSites.length > 0 ? 'hawaii' : 'domestic');
  } catch (error) {
    geocodeStatus.textContent = '데이터 로딩 실패';
    historicSiteStatus.textContent = '로딩 실패';
    courseList.innerHTML = '<div class="empty">루트 데이터를 불러오지 못했습니다.</div>';
    historicSiteList.innerHTML = '<div class="empty">진단 데이터를 불러오지 못했습니다.</div>';
  }
});

async function resolveCourseWaypoints(course) {
  const waypoints = await Promise.all(course.waypoints.map(resolveWaypoint));
  return { ...course, waypoints };
}

async function resolveWaypoint(waypoint) {
  const fallback = {
    lat: waypoint.fallbackLat,
    lng: waypoint.fallbackLng
  };

  if (waypoint.lockCoordinates) {
    return {
      ...waypoint,
      lat: fallback.lat,
      lng: fallback.lng,
      resolvedAddress: waypoint.address,
      geocoded: false
    };
  }

  try {
    const response = await fetch(`${GEOCODE_URL}?address=${encodeURIComponent(waypoint.address)}&key=${API_KEY}`);
    const data = await response.json();
    const result = Array.isArray(data.result) ? data.result[0] : null;
    const coords = getDriveableGeocodeCoords(result, fallback);

    return {
      ...waypoint,
      lat: coords.lat ?? fallback.lat,
      lng: coords.lng ?? fallback.lng,
      resolvedAddress: coords.formatted_address || waypoint.address,
      geocoded: Boolean(result)
    };
  } catch (error) {
    return {
      ...waypoint,
      lat: fallback.lat,
      lng: fallback.lng,
      resolvedAddress: waypoint.address,
      geocoded: false
    };
  }
}

function getDriveableGeocodeCoords(result, fallback) {
  const entrance = result?.street?.entrances?.[0];
  if (entrance?.lat != null && entrance?.lng != null) {
    return {
      ...result.street,
      lat: entrance.lat,
      lng: entrance.lng
    };
  }

  return result?.street || result?.jibun || fallback;
}

function setMapMode(mode) {
  if (!['domestic', 'hawaii'].includes(mode)) return;

  state.activeMapMode = mode;
  renderMapMode();

  if (mode === 'domestic') {
    state.activeHistoricSiteId = null;
    setHistoricSiteMarkersVisible(false);
    renderHistoricSiteList();

    if (state.courses.length > 0) {
      selectCourse(state.activeCourseId || state.courses[0].id);
    }
    return;
  }

  clearRouteMarkers();
  clearPoiMarker();
  resetCoursePanel();
  setHistoricSiteMarkersVisible(true);
  renderHistoricSiteList();
  fitHistoricSiteBounds();
  detailPanel.classList.remove('open');
}

function setLanguage(language) {
  if (!UI_TEXT[language]) return;

  state.language = language;
  document.documentElement.lang = language;
  renderLanguageControls();
  renderStaticText();
  if (state.historicSites.length > 0) {
    updateHistoricSiteCount();
  }
  renderCourseList();
  renderHistoricSiteList();

  if (state.activeMapMode === 'domestic' && state.activeCourseId) {
    const course = state.courses.find((item) => item.id === state.activeCourseId);
    if (course) {
      renderCourseSummary(course);
      renderWaypointList(course);

      if (state.activeWaypointId) {
        const waypointIndex = course.waypoints.findIndex((waypoint) => waypoint.id === state.activeWaypointId);
        const waypoint = course.waypoints[waypointIndex];
        if (waypoint) {
          openWaypointDetail(course, waypoint, waypointIndex);
        }
      } else {
        openCourseDetail(course);
      }
    }
  }

  if (state.activeHistoricSiteId) {
    openHistoricSiteDetail(state.historicSites.find((site) => site.id === state.activeHistoricSiteId));
  }
}

function renderMapMode() {
  mapModeTabs.forEach((button) => {
    button.classList.toggle('active', button.dataset.mapMode === state.activeMapMode);
  });

  domesticSections.forEach((section) => {
    section.hidden = state.activeMapMode !== 'domestic';
  });

  hawaiiSections.forEach((section) => {
    section.hidden = state.activeMapMode !== 'hawaii';
  });
}

function renderLanguageControls() {
  languageButtons.forEach((button) => {
    button.classList.toggle('active', button.dataset.language === state.language);
  });
}

function renderStaticText() {
  translatableElements.forEach((element) => {
    element.textContent = getUiText(element.dataset.i18n);
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach((element) => {
    element.placeholder = getUiText(element.dataset.i18nPlaceholder);
  });

  mapModeTabs.forEach((button) => {
    button.textContent = getUiText(button.dataset.mapMode);
  });
}

function getUiText(key, ...args) {
  const value = UI_TEXT[state.language]?.[key] ?? UI_TEXT.ko[key] ?? key;
  return typeof value === 'function' ? value(...args) : value;
}

function setHistoricSiteMarkersVisible(isVisible) {
  state.historicSiteMarkers.forEach(({ marker }) => {
    marker.getElement().hidden = !isVisible;
  });
}

function resetCoursePanel() {
  state.activeCourseId = null;
  state.activeWaypointId = null;
  renderCourseList();
  courseSummary.classList.add('empty');
  courseSummary.textContent = getUiText('courseEmpty');
  waypointList.innerHTML = '';
}

function getHistoricSiteText(site) {
  const translation = HAWAII_SITE_TRANSLATIONS[site.id]?.[state.language] || {};
  const uiText = UI_TEXT[state.language] || UI_TEXT.ko;
  const isKorean = state.language === 'ko';
  const significance = translation.significance || (isKorean ? site.historicalSignificance : uiText.genericSignificance);
  const status = translation.status || (isKorean ? site.currentStatus : uiText.genericStatus);

  return {
    name: translation.name || site.name,
    address: site.address || site.documentedAddress || uiText.noAddress,
    significance,
    status,
    description: buildHistoricSiteDescription(site, significance),
    type: uiText.historicType
  };
}

function getCourseText(course) {
  const translation = COURSE_TRANSLATIONS[course.id]?.[state.language] || {};

  return {
    title: translation.title || course.title,
    region: translation.region || course.region,
    creator: translation.creator || course.creator,
    theme: translation.theme || course.theme,
    difficulty: translation.difficulty || course.difficulty,
    description: translation.description || course.description
  };
}

function getWaypointText(waypoint) {
  const translation = WAYPOINT_TRANSLATIONS[waypoint.id]?.[state.language] || {};

  return {
    name: translation.name || waypoint.name,
    category: translation.category || waypoint.category,
    address: translation.address || waypoint.resolvedAddress || waypoint.address,
    description: translation.description || waypoint.description
  };
}

function buildHistoricSiteDescription(site, significance) {
  if (state.language === 'ko') {
    return `${significance}. ${UI_TEXT.ko.historicalTrace}`;
  }

  if (state.language === 'en') {
    return `${significance || 'This historic site is connected to the Korean community in Hawaii.'} ${UI_TEXT.en.historicalTrace}`;
  }

  if (state.language === 'zh') {
    return `${significance || '这里与夏威夷韩人社区历史有关。'}${UI_TEXT.zh.historicalTrace}`;
  }

  return `${significance || 'この場所はハワイ韓人社会の歴史と関わりがあります。'}${UI_TEXT.ja.historicalTrace}`;
}

function renderCourseList() {
  courseList.innerHTML = '';

  state.courses.forEach((course, index) => {
    const courseText = getCourseText(course);
    const time = getCourseTimeBreakdown(course, course.routeDurationSeconds);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'course-card';
    if (course.id === state.activeCourseId) {
      button.classList.add('active');
    }

    button.innerHTML = `
      <div class="course-card-header">
        <div>
          <h3>${courseText.title}</h3>
          <p class="course-description">${courseText.creator}</p>
        </div>
        <span class="course-tag">C${index + 1}</span>
      </div>
      <div class="course-meta">
        <span>${courseText.region}</span>
        <span>${formatMeters(course.routeDistanceMeters)}</span>
        <span>${time.totalText}</span>
        <span>${course.waypoints.length} stops</span>
      </div>
    `;

    button.addEventListener('click', () => selectCourse(course.id));
    courseList.appendChild(button);
  });
}

function selectCourse(courseId) {
  state.activeMapMode = 'domestic';
  state.activeCourseId = courseId;
  state.activeWaypointId = null;
  state.activeHistoricSiteId = null;
  renderMapMode();
  setHistoricSiteMarkersVisible(false);
  renderCourseList();
  renderHistoricSiteList();
  updateHistoricSiteMarkers();

  const course = state.courses.find((item) => item.id === courseId);
  if (!course) return;

  const courseText = getCourseText(course);
  renderCourseSummary(course);
  renderWaypointList(course);
  drawCourse(course);
  openCourseDetail(course);
}

function openCourseDetail(course) {
  const courseText = getCourseText(course);
  openDetail({
    badge: 'COURSE',
    kicker: courseText.region,
    name: courseText.title,
    address: `${courseText.creator} | ${getCourseTimeBreakdown(course, course.routeDurationSeconds).totalText}`,
    description: courseText.description,
    type: `${courseText.theme} | ${courseText.difficulty}`,
    lat: course.waypoints[0]?.lat,
    lng: course.waypoints[0]?.lng
  });
}

function updateHistoricSiteCount() {
  const ui = UI_TEXT[state.language] || UI_TEXT.ko;
  const targetCount = state.historicSites.filter((site) => site.tier !== 'metro').length;
  const metroCount = state.historicSites.length - targetCount;
  historicSiteStatus.textContent = ui.siteCount(targetCount) + (metroCount ? ui.metroSuffix(metroCount) : '');
}

function renderHistoricSiteList() {
  historicSiteList.innerHTML = '';

  if (state.historicSites.length === 0) {
    historicSiteList.innerHTML = `<div class="empty">${getUiText('noSites')}</div>`;
    return;
  }

  state.historicSites.forEach((site) => {
    const siteText = getHistoricSiteText(site);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'historic-site-card';
    if (site.tier === 'metro') {
      button.classList.add('metro');
    }
    if (site.id === state.activeHistoricSiteId) {
      button.classList.add('active');
    }

    button.innerHTML = `
      <div class="historic-site-card-header">
        <div>
          <h3>${siteText.name}</h3>
          <p class="historic-site-address">${siteText.address}</p>
        </div>
        <span class="historic-site-tag">${site.number}</span>
      </div>
      <div class="historic-site-meta">
        <span>${siteText.type}</span>
        <span>${siteText.status || getUiText('currentStatus')}</span>
      </div>
    `;

    button.addEventListener('click', () => selectHistoricSite(site.id, true));
    historicSiteList.appendChild(button);
  });
}

function selectHistoricSite(siteId, shouldFlyTo = false) {
  const site = state.historicSites.find((item) => item.id === siteId);
  if (!site) return;

  state.activeMapMode = 'hawaii';
  state.activeCourseId = null;
  state.activeWaypointId = null;
  state.activeHistoricSiteId = site.id;
  renderMapMode();
  renderCourseList();
  courseSummary.classList.add('empty');
  courseSummary.textContent = getUiText('courseEmpty');
  waypointList.innerHTML = '';
  renderHistoricSiteList();
  setHistoricSiteMarkersVisible(true);
  updateHistoricSiteMarkers();
  clearRouteMarkers();
  clearPoiMarker();
  openHistoricSiteDetail(site);

  if (shouldFlyTo) {
    map.flyTo({ center: [site.lng, site.lat], zoom: 13.6, duration: 900 });
  }
}

function drawHistoricSites() {
  clearHistoricSiteMarkers();

  state.historicSites.forEach((site) => {
    const marker = new routogl.Marker({ element: createHistoricSiteMarkerElement(site) })
      .setLngLat([site.lng, site.lat])
      .addTo(map);

    marker.getElement().addEventListener('click', (event) => {
      event.stopPropagation();
      selectHistoricSite(site.id, false);
    });

    state.historicSiteMarkers.push({ siteId: site.id, marker });
  });
}

function fitHistoricSiteBounds() {
  const firstSite = state.historicSites[0];
  if (!firstSite) return;

  const bounds = new routogl.LngLatBounds([firstSite.lng, firstSite.lat], [firstSite.lng, firstSite.lat]);
  state.historicSites.forEach((site) => bounds.extend([site.lng, site.lat]));
  map.fitBounds(bounds, {
    padding: { top: 60, right: 420, bottom: 60, left: 60 },
    duration: 900
  });
}

function clearHistoricSiteMarkers() {
  state.historicSiteMarkers.forEach(({ marker }) => marker.remove());
  state.historicSiteMarkers = [];
}

function updateHistoricSiteMarkers() {
  state.historicSiteMarkers.forEach(({ siteId, marker }) => {
    marker.getElement().classList.toggle('active', siteId === state.activeHistoricSiteId);
  });
}

function createHistoricSiteMarkerElement(site) {
  const element = document.createElement('button');
  element.type = 'button';
  element.className = 'historic-site-marker';
  if (site.tier === 'metro') {
    element.classList.add('metro');
  }
  if (site.populationDecline) {
    element.classList.add('decline');
  }
  element.setAttribute('aria-label', `${site.name} 진단 결과 보기`);
  element.innerHTML = `<span class="historic-site-marker-pin"><span>${site.number}</span></span>`;
  return element;
}

function isValidHistoricSite(site) {
  return site
    && site.name
    && Number.isFinite(site.lat)
    && Number.isFinite(site.lng);
}

function renderCourseSummary(course) {
  const courseText = getCourseText(course);
  const time = getCourseTimeBreakdown(course, course.routeDurationSeconds);
  courseSummary.classList.remove('empty');
  courseSummary.innerHTML = `
    <h3 class="summary-title">${courseText.title}</h3>
    <p class="summary-copy">${courseText.description}</p>
    <p class="search-meta">${getUiText('totalDuration')} ${time.totalText} = ${getUiText('drive')} ${time.driveText} + ${getUiText('recommendedStay')} ${time.stayText}</p>
    <dl class="summary-grid">
      <div>
        <dt>${getUiText('creator')}</dt>
        <dd>${courseText.creator}</dd>
      </div>
      <div>
        <dt>${getUiText('courseType')}</dt>
        <dd>${courseText.theme}</dd>
      </div>
      <div>
        <dt>${getUiText('totalDistance')}</dt>
        <dd>${formatMeters(course.routeDistanceMeters)}</dd>
      </div>
      <div>
        <dt>${getUiText('totalDuration')}</dt>
        <dd>${time.totalText}</dd>
      </div>
    </dl>
  `;
}

function renderWaypointList(course) {
  waypointList.innerHTML = '';

  course.waypoints.forEach((waypoint, index) => {
    const waypointText = getWaypointText(waypoint);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'waypoint-card';
    if (waypoint.id === state.activeWaypointId) {
      button.classList.add('active');
    }

    const thumb = waypoint.imageUrl
      ? `<span class="waypoint-thumb" style="background-image:url('${waypoint.imageUrl}')"></span>`
      : '';

    button.innerHTML = `
      <div class="waypoint-card-header">
        ${thumb}
        <div class="waypoint-card-text">
          <h3>${waypointText.name}</h3>
          <p class="waypoint-address">${waypointText.address}</p>
        </div>
        <span class="order-badge">${index + 1}</span>
      </div>
      <div class="waypoint-meta">
        <span>${waypointText.category}</span>
        <span>${formatStay(waypoint.stay)}</span>
      </div>
    `;

    button.addEventListener('click', () => {
      state.activeWaypointId = waypoint.id;
      renderWaypointList(course);
      openWaypointDetail(course, waypoint, index);
      map.flyTo({ center: [waypoint.lng, waypoint.lat], zoom: 11.8, duration: 900 });
    });

    waypointList.appendChild(button);
  });
}

async function drawCourse(course) {
  clearRouteMarkers();
  clearPoiMarker();

  const coordinates = course.waypoints.map((waypoint) => [waypoint.lng, waypoint.lat]);
  const bounds = new routogl.LngLatBounds(coordinates[0], coordinates[0]);
  const requestToken = ++state.routeRequestToken;

  course.waypoints.forEach((waypoint, index) => {
    const marker = new routogl.Marker({ element: createCourseMarkerElement(waypoint, index) })
      .setLngLat([waypoint.lng, waypoint.lat])
      .addTo(map);

    const element = marker.getElement();
    element.addEventListener('click', (event) => {
      event.stopPropagation();
      state.activeWaypointId = waypoint.id;
      renderWaypointList(course);
      openWaypointDetail(course, waypoint, index);
    });

    state.routeMarkers.push(marker);
    bounds.extend([waypoint.lng, waypoint.lat]);
  });

  if (Array.isArray(course.routePath)) {
    course.routePath.forEach((point) => bounds.extend(point));
  }

  const routeResult = await fetchDirectionsRoute(course);
  if (requestToken !== state.routeRequestToken || course.id !== state.activeCourseId) {
    return;
  }

  const routeGeoJson = {
    type: 'Feature',
    properties: routeResult.summary || {},
    geometry: getRouteLineGeometry(routeResult.coordinates.length > 1 ? routeResult.coordinates : coordinates)
  };

  if (map.getLayer('course-route-line')) {
    map.removeLayer('course-route-line');
  }

  if (map.getSource('course-route')) {
    map.removeSource('course-route');
  }

  map.addSource('course-route', {
    type: 'geojson',
    data: routeGeoJson
  });

  map.addLayer({
    id: 'course-route-line',
    type: 'line',
    source: 'course-route',
    layout: {
      'line-cap': 'round',
      'line-join': 'round'
    },
    paint: {
      'line-color': '#1f1f1f',
      'line-width': 5,
      'line-opacity': 0.86
    }
  });

  updateCourseSummary(course, routeResult);
  map.fitBounds(bounds, {
    padding: { top: 60, right: 420, bottom: 60, left: 60 },
    duration: 900
  });
}

function clearRouteMarkers() {
  state.routeMarkers.forEach((marker) => marker.remove());
  state.routeMarkers = [];

  if (map.getLayer('course-route-line')) {
    map.removeLayer('course-route-line');
  }

  if (map.getSource('course-route')) {
    map.removeSource('course-route');
  }
}

function createCourseMarkerElement(waypoint, index) {
  const element = document.createElement('button');
  element.type = 'button';
  element.className = 'course-marker';
  element.setAttribute('aria-label', `${getWaypointText(waypoint).name} 보기`);
  const photoStyle = waypoint.imageUrl ? ` style="background-image: url('${waypoint.imageUrl}');"` : '';
  element.innerHTML = `
    <span class="course-marker-photo${waypoint.imageUrl ? '' : ' empty'}"${photoStyle}>${waypoint.imageUrl ? '' : index + 1}</span>
    <span class="course-marker-pin">${index + 1}</span>
  `;
  return element;
}

function getRouteLineGeometry(coordinates) {
  const uniqueSegments = getUniqueRouteSegments(coordinates);

  if (uniqueSegments.length > 0) {
    return {
      type: 'MultiLineString',
      coordinates: uniqueSegments
    };
  }

  return {
    type: 'LineString',
    coordinates
  };
}

function getUniqueRouteSegments(coordinates) {
  const seenSegments = new Set();
  const segments = [];

  coordinates.slice(1).forEach((coordinate, index) => {
    const previous = coordinates[index];
    if (!isValidCoordinate(previous) || !isValidCoordinate(coordinate)) return;
    if (previous[0] === coordinate[0] && previous[1] === coordinate[1]) return;

    const segmentKey = getSegmentKey(previous, coordinate);
    if (seenSegments.has(segmentKey)) return;

    seenSegments.add(segmentKey);
    segments.push([previous, coordinate]);
  });

  return segments;
}

function getSegmentKey(from, to) {
  const fromKey = getCoordinateKey(from);
  const toKey = getCoordinateKey(to);
  return [fromKey, toKey].sort().join('|');
}

function getCoordinateKey(coordinate) {
  return `${coordinate[0].toFixed(7)},${coordinate[1].toFixed(7)}`;
}

function isValidCoordinate(coordinate) {
  return Array.isArray(coordinate)
    && coordinate.length === 2
    && Number.isFinite(coordinate[0])
    && Number.isFinite(coordinate[1]);
}

async function fetchDirectionsRoute(course) {
  // 방문 순서대로 좌표를 이어 OSRM에 실도로 경로를 요청 (무료·무키)
  const points = course.waypoints
    .filter((w) => Number.isFinite(w.lng) && Number.isFinite(w.lat))
    .map((w) => `${w.lng},${w.lat}`);

  if (points.length < 2) {
    return buildFallbackRoute(course, '경유지 좌표가 부족해 직선 경로선을 표시합니다.');
  }

  try {
    const url = `${OSRM_URL}/${points.join(';')}?overview=full&geometries=geojson`;
    const response = await fetch(url);

    if (!response.ok) {
      const errorText = await response.text();
      return buildFallbackRoute(course, formatDirectionsError(response.status, errorText));
    }

    const data = await response.json();
    const route = data && data.code === 'Ok' && Array.isArray(data.routes) ? data.routes[0] : null;
    const routeCoordinates = Array.isArray(route?.geometry?.coordinates)
      ? route.geometry.coordinates.filter((p) => Number.isFinite(p[0]) && Number.isFinite(p[1]))
      : [];

    return {
      coordinates: routeCoordinates.length > 1 ? routeCoordinates : getManualRoutePath(course),
      fallback: routeCoordinates.length < 2,
      errorMessage: routeCoordinates.length < 2 ? '도로 경로를 해석하지 못해 직선 경로선을 표시합니다.' : '',
      summary: route ? { distanceMeters: Math.round(route.distance), durationSeconds: Math.round(route.duration) } : null
    };
  } catch (error) {
    return buildFallbackRoute(course, 'OSRM 경로 호출에 실패해 직선 경로선을 표시합니다.');
  }
}

function buildFallbackRoute(course, errorMessage) {
  const manualPath = getManualRoutePath(course);

  return {
    coordinates: manualPath.length > 1 ? manualPath : course.waypoints.map((waypoint) => [waypoint.lng, waypoint.lat]),
    fallback: true,
    errorMessage: manualPath.length > 1 ? errorMessage : `${errorMessage} 수동 경로선이 없어 경유지를 직접 연결합니다.`,
    summary: null
  };
}

function getManualRoutePath(course) {
  if (!Array.isArray(course.routePath)) return [];

  const routePath = course.routePath
    .filter((point) => Array.isArray(point) && point.length === 2)
    .filter((point) => Number.isFinite(point[0]) && Number.isFinite(point[1]));

  return anchorRoutePathToWaypoints(routePath, course.waypoints);
}

function anchorRoutePathToWaypoints(routePath, waypoints) {
  if (routePath.length < 2 || !Array.isArray(waypoints) || waypoints.length === 0) {
    return routePath;
  }

  const anchoredPath = routePath.map((point) => [...point]);

  waypoints.forEach((waypoint, waypointIndex) => {
    const waypointCoord = [waypoint.lng, waypoint.lat];
    if (!Number.isFinite(waypointCoord[0]) || !Number.isFinite(waypointCoord[1])) return;

    if (waypointIndex === 0) {
      anchoredPath[0] = waypointCoord;
      return;
    }

    if (waypointIndex === waypoints.length - 1) {
      anchoredPath[anchoredPath.length - 1] = waypointCoord;
      return;
    }

    const closestIndex = findClosestPathIndex(anchoredPath, waypointCoord);
    anchoredPath.splice(closestIndex + 1, 0, waypointCoord);
  });

  return anchoredPath;
}

function findClosestPathIndex(routePath, coordinate) {
  let closestIndex = 0;
  let closestDistance = Infinity;

  routePath.forEach((point, index) => {
    const dx = point[0] - coordinate[0];
    const dy = point[1] - coordinate[1];
    const distance = dx * dx + dy * dy;

    if (distance < closestDistance) {
      closestDistance = distance;
      closestIndex = index;
    }
  });

  return closestIndex;
}

function toRoutePoint(waypoint, fallbackName) {
  return {
    YPos: waypoint.lat,
    XPos: waypoint.lng,
    Name: waypoint.name || fallbackName
  };
}

function formatDirectionsError(status, rawText) {
  if (status === 401) {
    return 'Directions 권한이 없어 수동 경로선을 표시합니다.';
  }

  try {
    const payload = JSON.parse(rawText);
    if (payload.ResultStr) {
      return `Directions 실패: ${payload.ResultStr}`;
    }
    if (payload.message) {
      return `Directions 실패: ${payload.message}`;
    }
  } catch (error) {
    // Ignore JSON parse errors and use generic message below.
  }

  return `Directions API 오류(${status})로 수동 경로선을 표시합니다.`;
}

function updateCourseSummary(course, routeResult) {
  const courseText = getCourseText(course);
  const summaryDistance = Number.isFinite(routeResult.summary?.distanceMeters)
    ? formatMeters(routeResult.summary.distanceMeters)
    : Number.isFinite(course.routeDistanceMeters)
      ? formatMeters(course.routeDistanceMeters)
    : routeResult.coordinates.length > 1
      ? formatMeters(getPathDistanceMeters(routeResult.coordinates))
      : course.distance;
  const summaryDuration = Number.isFinite(routeResult.summary?.durationSeconds)
    ? Number(routeResult.summary.durationSeconds)
    : Number.isFinite(course.routeDurationSeconds)
      ? course.routeDurationSeconds
    : null;
  const time = getCourseTimeBreakdown(course, summaryDuration);
  const routeStatus = routeResult.fallback
    ? routeResult.errorMessage
    : getUiText('routeStatusFallback');

  courseSummary.classList.remove('empty');
  courseSummary.innerHTML = `
    <h3 class="summary-title">${courseText.title}</h3>
    <p class="summary-copy">${courseText.description}</p>
    <p class="search-meta">${routeStatus}</p>
    <dl class="summary-grid">
      <div>
        <dt>${getUiText('creator')}</dt>
        <dd>${courseText.creator}</dd>
      </div>
      <div>
        <dt>${getUiText('courseType')}</dt>
        <dd>${courseText.theme}</dd>
      </div>
      <div>
        <dt>${getUiText('totalDistance')}</dt>
        <dd>${summaryDistance}</dd>
      </div>
      <div>
        <dt>${getUiText('totalDuration')}</dt>
        <dd>${time.totalText}</dd>
      </div>
    </dl>
    <p class="search-meta">${getUiText('drive')} ${time.driveText} + ${getUiText('recommendedStay')} ${time.stayText}</p>
  `;
}

function getCourseTimeBreakdown(course, driveSeconds) {
  const normalizedDriveSeconds = Number.isFinite(driveSeconds) ? driveSeconds : 0;
  const stayMinutes = getCourseStayMinutes(course);
  const driveMinutes = Math.round(normalizedDriveSeconds / 60);
  const totalMinutes = driveMinutes + stayMinutes;

  return {
    driveText: formatMinutes(driveMinutes),
    stayText: formatMinutes(stayMinutes),
    totalText: formatMinutes(totalMinutes)
  };
}

function getCourseStayMinutes(course) {
  return course.waypoints.reduce((total, waypoint) => {
    const match = String(waypoint.stay || '').match(/\d+/);
    return total + (match ? Number(match[0]) : 0);
  }, 0);
}

function formatMinutes(minutes) {
  if (!Number.isFinite(minutes)) return '-';

  const roundedMinutes = Math.max(0, Math.round(minutes));
  const hours = Math.floor(roundedMinutes / 60);
  const remainingMinutes = roundedMinutes % 60;

  if (state.language === 'en') {
    const parts = [];
    if (hours > 0) parts.push(`${hours} hr`);
    if (remainingMinutes > 0 || parts.length === 0) parts.push(`${remainingMinutes} min`);
    return parts.join(' ');
  }

  if (state.language === 'zh') {
    if (hours > 0 && remainingMinutes > 0) return `${hours}小时 ${remainingMinutes}分钟`;
    if (hours > 0) return `${hours}小时`;
    return `${remainingMinutes}分钟`;
  }

  if (state.language === 'ja') {
    if (hours > 0 && remainingMinutes > 0) return `${hours}時間 ${remainingMinutes}分`;
    if (hours > 0) return `${hours}時間`;
    return `${remainingMinutes}分`;
  }

  if (hours > 0 && remainingMinutes > 0) {
    return `${hours}시간 ${remainingMinutes}분`;
  }

  if (hours > 0) {
    return `${hours}시간`;
  }

  return `${remainingMinutes}분`;
}

function formatMeters(value) {
  const distance = Number(value);
  if (!Number.isFinite(distance)) return `${value}`;
  if (distance >= 1000) {
    const kilometers = (distance / 1000).toFixed(1);
    if (state.language === 'zh') return `${kilometers}公里`;
    if (state.language === 'ja') return `${kilometers}km`;
    return `${kilometers}km`;
  }

  const meters = Math.round(distance);
  if (state.language === 'zh') return `${meters}米`;
  return `${meters}m`;
}

function formatStay(value) {
  const match = String(value || '').match(/\d+/);
  if (!match) return value || '-';
  return formatMinutes(Number(match[0]));
}

function formatSeconds(value) {
  const totalSeconds = Number(value);
  if (!Number.isFinite(totalSeconds)) return `${value}`;

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.round((totalSeconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}시간 ${minutes}분`;
  }

  return `${minutes}분`;
}

function getPathDistanceMeters(coordinates) {
  return coordinates.slice(1).reduce((total, coordinate, index) => {
    return total + getHaversineDistanceMeters(coordinates[index], coordinate);
  }, 0);
}

function getHaversineDistanceMeters(from, to) {
  const earthRadiusMeters = 6371000;
  const fromLat = toRadians(from[1]);
  const toLat = toRadians(to[1]);
  const deltaLat = toRadians(to[1] - from[1]);
  const deltaLng = toRadians(to[0] - from[0]);

  const a = Math.sin(deltaLat / 2) ** 2
    + Math.cos(fromLat) * Math.cos(toLat) * Math.sin(deltaLng / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return earthRadiusMeters * c;
}

function toRadians(value) {
  return value * Math.PI / 180;
}

function renderPoiResults(results) {
  poiResults.innerHTML = '';

  if (results.length === 0) {
    poiResults.innerHTML = `<div class="empty">${getUiText('noSearchResults')}</div>`;
    return;
  }

  results.forEach((poi, index) => {
    const poiText = getPoiText(poi);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'poi-card';
    button.innerHTML = `
      <div class="poi-card-header">
        <div>
          <h3>${poiText.title}</h3>
          <p class="poi-address">${poiText.address}</p>
        </div>
        <span class="poi-tag">${index + 1}</span>
      </div>
      <div class="poi-meta">
        <span>${poiText.categoryTop}</span>
        <span>${poi.tele || getUiText('noPhone')}</span>
      </div>
    `;

    button.addEventListener('click', () => {
      const lat = poi.guide?.lat ?? poi.center?.lat;
      const lng = poi.guide?.lon ?? poi.center?.lon;
      if (lat == null || lng == null) return;

      showPoiMarker(lng, lat);
      map.flyTo({ center: [lng, lat], zoom: 12.5, duration: 900 });
      openDetail({
        badge: 'POI',
        kicker: 'Journey Search',
        name: poiText.title,
        address: poiText.address,
        description: `${poiText.category} | ${poiText.categoryTop}`,
        type: poi.classCode || 'poi',
        lat,
        lng
      });
    });

    poiResults.appendChild(button);
  });
}

function getPoiText(poi) {
  return {
    title: pickLocalizedPoiField(poi, ['titleEng', 'titleEn', 'nameEng', 'nameEn', 'engName', 'title']) || poi.title || getUiText('place'),
    address: pickLocalizedPoiField(poi, ['addrRoadEng', 'addrEng', 'addressEng', 'addrRoad', 'addr']) || getUiText('noAddress'),
    category: pickLocalizedPoiField(poi.classNameInfo || {}, ['classNameEng', 'classNameEn', 'className']) || getUiText('place'),
    categoryTop: pickLocalizedPoiField(poi.classNameInfo || {}, ['classNameTopEng', 'classNameTopEn', 'classNameTop']) || getUiText('noCategory')
  };
}

function pickLocalizedPoiField(source, fieldNames) {
  if (!source) return '';

  if (state.language === 'ko') {
    return fieldNames.map((field) => source[field]).find(Boolean) || '';
  }

  const preferred = fieldNames.filter((field) => /eng|en/i.test(field));
  return [...preferred, ...fieldNames].map((field) => source[field]).find(Boolean) || '';
}

function showPoiMarker(lng, lat) {
  clearPoiMarker();
  state.poiMarker = new routogl.Marker({ color: '#1f1f1f' })
    .setLngLat([lng, lat])
    .addTo(map);
}

function clearPoiMarker() {
  if (state.poiMarker) {
    state.poiMarker.remove();
    state.poiMarker = null;
  }
}

function openWaypointDetail(course, waypoint, index) {
  const courseText = getCourseText(course);
  const waypointText = getWaypointText(waypoint);
  openDetail({
    badge: `STOP ${index + 1}`,
    kicker: courseText.title,
    name: waypointText.name,
    address: courseText.region,
    fullAddress: waypointText.address,
    imageUrl: waypoint.imageUrl,
    description: waypointText.description,
    type: `${waypointText.category} | ${formatStay(waypoint.stay)}`,
    lat: waypoint.lat,
    lng: waypoint.lng
  });
}

function openHistoricSiteDetail(site) {
  if (!site) return;

  const siteText = getHistoricSiteText(site);
  openDetail({
    badge: `SITE ${site.number}`,
    kicker: getUiText('hawaiiSites'),
    name: siteText.name,
    address: siteText.address,
    description: siteText.description,
    typeLabel: getUiText('currentStatus'),
    type: siteText.status || getUiText('currentStatus'),
    lat: site.lat,
    lng: site.lng
  });
}

function openDetail(item) {
  detailBadge.textContent = item.badge || 'DETAIL';
  detailKicker.textContent = item.kicker || '';
  detailName.textContent = item.name || '';
  detailAddress.textContent = item.address || '';
  detailDescription.textContent = item.description || '';
  detailTypeLabel.textContent = item.typeLabel || getUiText('detailType');
  detailType.textContent = item.type || '';

  const hasAddress = Boolean(item.fullAddress);
  detailCoordsLabel.textContent = hasAddress ? getUiText('addressLabel') : getUiText('coords');
  detailCoords.textContent = hasAddress
    ? item.fullAddress
    : (item.lat != null && item.lng != null
        ? `${Number(item.lat).toFixed(5)}, ${Number(item.lng).toFixed(5)}`
        : '-');

  if (detailMedia) {
    if (item.imageUrl) {
      detailMedia.style.backgroundImage = `url('${item.imageUrl}')`;
      detailMedia.classList.add('has-photo');
    } else {
      detailMedia.style.backgroundImage = '';
      detailMedia.classList.remove('has-photo');
    }
  }

  detailPanel.classList.add('open');
}
