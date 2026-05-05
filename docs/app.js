(() => {
  const state = {
    lang: localStorage.getItem("power_age_lang") || "ru",
    tab: "initiator_group_x_decision_domain",
    datasetId: localStorage.getItem("power_age_dataset") || "",
    datasets: [],
    dataset: null,
    data: null,
  };

  const DATASETS_URL = "data/datasets.json";
  const FALLBACK_DATASET = {
    id: "russia",
    label: { ru: "Россия / СССР", en: "Russia / USSR" },
    description: {
      ru: "Текущий набор данных по возрасту элиты, фракциям и событиям для России и СССР.",
      en: "Current dataset covering elite age, factions, and events for Russia and the USSR.",
    },
    data_url: "data/site-data.json",
  };

  const I18N = {
    ru: {
      title: "Power Age",
      lead:
        "Исследовательский прототип о возрасте элиты, фракциях и событиях в России и СССР. Страница собирает графики, корреляционные выводы, кросс-табы и событийный слой в одном месте.",
      nav: {
        overview: "Обзор",
        correlations: "Корреляции",
        core: "Элита",
        factions: "Фракции",
        events: "События",
        crosstabs: "Кросс-табы",
        notes: "Примечания",
      },
      sections: {
        overview: "Обзор",
        correlations: "Выводы по корреляциям",
        core: "Возраст элиты и правителя",
        factions: "Фракционный слой",
        events: "Событийный слой",
        crosstabs: "Плотные кросс-табы",
        notes: "Ограничения",
      },
      meta: {
        years: "годы",
        persons: "персон",
        events: "событий",
        eliteEvents: "elite-initiated",
        factions: "фракций",
      },
      footer:
        'Собрано из CSV в <code>data/raw</code>. Нажмите на любую картинку, чтобы открыть увеличенную версию. Статический сайт предназначен для GitHub Pages.',
      crosstabLabel: {
        initiator_group_x_decision_domain: "initiator_group x decision_domain",
        faction_type_x_decision_domain: "faction_type x decision_domain",
      },
      crosstabDescription: {
        initiator_group_x_decision_domain:
          "Как группы-инициаторы соотносятся с доменами решений.",
        faction_type_x_decision_domain:
          "Как типы фракций распределяются по доменам решений.",
      },
      eventNavLabel: "Быстрая навигация по событиям",
      periodsLabel: "Периоды",
      severityLabel: "Ключевые severity=5",
      strongestLabel: "Самые сильные связи",
      figureClick: "Нажмите для увеличения",
      lightboxTitle: "График",
      close: "Закрыть",
      tableRows: "строки",
      tableCols: "столбцы",
    },
    en: {
      title: "Power Age",
      lead:
        "A research prototype on elite age, factions, and events in Russia and the USSR. The page brings charts, correlation takeaways, cross-tabs, and the event layer into one place.",
      nav: {
        overview: "Overview",
        correlations: "Correlations",
        core: "Elite",
        factions: "Factions",
        events: "Events",
        crosstabs: "Cross-tabs",
        notes: "Notes",
      },
      sections: {
        overview: "Overview",
        correlations: "Correlation takeaways",
        core: "Elite age and ruler age",
        factions: "Faction layer",
        events: "Event layer",
        crosstabs: "Dense cross-tabs",
        notes: "Notes",
      },
      meta: {
        years: "years",
        persons: "persons",
        events: "events",
        eliteEvents: "elite-initiated",
        factions: "factions",
      },
      footer:
        'Built from CSV files in <code>data/raw</code>. Click any image to open a larger view. This static site is designed for GitHub Pages.',
      crosstabLabel: {
        initiator_group_x_decision_domain: "initiator_group x decision_domain",
        faction_type_x_decision_domain: "faction_type x decision_domain",
      },
      crosstabDescription: {
        initiator_group_x_decision_domain:
          "How initiating groups map onto decision domains.",
        faction_type_x_decision_domain:
          "How faction types distribute across decision domains.",
      },
      eventNavLabel: "Quick event navigation",
      periodsLabel: "Periods",
      severityLabel: "Key severity=5",
      strongestLabel: "Strongest correlations",
      figureClick: "Click to enlarge",
      lightboxTitle: "Figure",
      close: "Close",
      tableRows: "rows",
      tableCols: "cols",
    },
  };

  const FIGURE_GROUPS = [
    {
      id: "core",
      sectionId: "core",
      figures: [
        {
          id: "core_elite_aging_dashboard",
          src: "figures/core_elite_aging_dashboard.png",
          wide: true,
          title: {
            ru: "Панель старения core elite",
            en: "Core elite aging dashboard",
          },
          caption: {
            ru: "Средний возраст, 60+/70+, renewal_5y и размер ядра власти.",
            en: "Mean age, 60+/70+, renewal_5y, and core size.",
          },
        },
        {
          id: "ruler_age_timeline",
          src: "figures/ruler_age_timeline.png",
          title: {
            ru: "Возраст правителя и события",
            en: "Ruler age and events",
          },
          caption: {
            ru: "Линия возраста правителя с историческими событиями на шкале времени.",
            en: "Ruler age with historical events over time.",
          },
        },
        {
          id: "ruler_vs_core_age",
          src: "figures/ruler_vs_core_age.png",
          title: {
            ru: "Правитель против core elite",
            en: "Ruler vs core elite",
          },
          caption: {
            ru: "Сравнение возраста правителя со средним и взвешенным возрастом ядра власти.",
            en: "Ruler age compared with mean and weighted core age.",
          },
        },
        {
          id: "biological_vs_political_age",
          src: "figures/biological_vs_political_age.png",
          title: {
            ru: "Биологический и политический возраст",
            en: "Biological and political age",
          },
          caption: {
            ru: "Разделение физического возраста и длительности нахождения в политическом контуре.",
            en: "Physical age versus time spent inside the political system.",
          },
        },
        {
          id: "core_elite_age",
          src: "figures/core_elite_age.png",
          title: {
            ru: "Средний возраст core elite",
            en: "Average core elite age",
          },
          caption: {
            ru: "Обычное и influence-weighted среднее по активной core elite.",
            en: "Plain and influence-weighted averages for the active core elite.",
          },
        },
        {
          id: "period_age_boxplots",
          src: "figures/period_age_boxplots.png",
          title: {
            ru: "Возраст по периодам",
            en: "Age by period",
          },
          caption: {
            ru: "Распределение возраста core elite по историческим периодам.",
            en: "Core elite age distributions by historical period.",
          },
        },
        {
          id: "institution_composition",
          src: "figures/institution_composition.png",
          wide: true,
          title: {
            ru: "Институциональный состав",
            en: "Institutional composition",
          },
          caption: {
            ru: "Доли институтов по сумме influence_weight в активной core elite.",
            en: "Institution shares by influence_weight in the active core elite.",
          },
        },
      ],
    },
    {
      id: "factions",
      sectionId: "factions",
      figures: [
        {
          id: "faction_power_share_stacked",
          src: "figures/faction_power_share_stacked.png",
          wide: true,
          title: {
            ru: "Фракционная власть",
            en: "Faction power",
          },
          caption: {
            ru: "Stacked area chart по normalized_power_share.",
            en: "Stacked area chart of normalized_power_share.",
          },
        },
        {
          id: "faction_type_power_share_stacked",
          src: "figures/faction_type_power_share_stacked.png",
          wide: true,
          title: {
            ru: "Фракционная власть по типам",
            en: "Faction power by type",
          },
          caption: {
            ru: "Сравнимый между эпохами слой типов фракционной логики.",
            en: "A comparable across-epochs layer of faction logic types.",
          },
        },
        {
          id: "faction_fragmentation",
          src: "figures/faction_fragmentation.png",
          title: {
            ru: "Индекс фрагментации",
            en: "Fragmentation index",
          },
          caption: {
            ru: "1 - sum(normalized_power_share^2).",
            en: "1 - sum(normalized_power_share^2).",
          },
        },
        {
          id: "faction_power_heatmap",
          src: "figures/faction_power_heatmap.png",
          title: {
            ru: "Heatmap фракционной власти",
            en: "Faction power heatmap",
          },
          caption: {
            ru: "Год x фракция по normalized_power_share.",
            en: "Year by faction heatmap of normalized_power_share.",
          },
        },
        {
          id: "faction_mean_age",
          src: "figures/faction_mean_age.png",
          title: {
            ru: "Средний возраст фракций",
            en: "Faction mean age",
          },
          caption: {
            ru: "Средний биологический возраст по фракциям.",
            en: "Mean biological age by faction.",
          },
        },
        {
          id: "faction_weighted_mean_age",
          src: "figures/faction_weighted_mean_age.png",
          title: {
            ru: "Взвешенный возраст фракций",
            en: "Weighted faction age",
          },
          caption: {
            ru: "Взвешенный по influence_weight возраст фракций.",
            en: "Influence-weighted faction age.",
          },
        },
      ],
    },
    {
      id: "faction-periods",
      sectionId: "factions",
      figures: [
        {
          id: "factions_empire_1801_1917",
          src: "figures/factions_empire_1801_1917.png",
          title: {
            ru: "Российская империя",
            en: "Russian Empire",
          },
          caption: {
            ru: "1801-1917.",
            en: "1801-1917.",
          },
        },
        {
          id: "factions_revolution_1917_1924",
          src: "figures/factions_revolution_1917_1924.png",
          title: {
            ru: "Революция и ранний СССР",
            en: "Revolution / early Soviet",
          },
          caption: {
            ru: "1917-1924.",
            en: "1917-1924.",
          },
        },
        {
          id: "factions_stalin_1924_1953",
          src: "figures/factions_stalin_1924_1953.png",
          title: {
            ru: "Сталинский период",
            en: "Stalin era",
          },
          caption: {
            ru: "1924-1953.",
            en: "1924-1953.",
          },
        },
        {
          id: "factions_poststalin_1953_1964",
          src: "figures/factions_poststalin_1953_1964.png",
          title: {
            ru: "Постсталинский период",
            en: "Post-Stalin / Khrushchev",
          },
          caption: {
            ru: "1953-1964.",
            en: "1953-1964.",
          },
        },
        {
          id: "factions_lateussr_1964_1985",
          src: "figures/factions_lateussr_1964_1985.png",
          title: {
            ru: "Поздний СССР",
            en: "Late Soviet",
          },
          caption: {
            ru: "1964-1985.",
            en: "1964-1985.",
          },
        },
        {
          id: "factions_perestroika_1985_1991",
          src: "figures/factions_perestroika_1985_1991.png",
          title: {
            ru: "Перестройка",
            en: "Perestroika",
          },
          caption: {
            ru: "1985-1991.",
            en: "1985-1991.",
          },
        },
        {
          id: "factions_rf_1991_2026",
          src: "figures/factions_rf_1991_2026.png",
          title: {
            ru: "Российская Федерация",
            en: "Russian Federation",
          },
          caption: {
            ru: "1991-2026.",
            en: "1991-2026.",
          },
        },
      ],
    },
    {
      id: "events",
      sectionId: "events",
      figures: [
        {
          id: "events_by_year",
          src: "figures/events_by_year.png",
          wide: true,
          title: {
            ru: "События по годам",
            en: "Events by year",
          },
          caption: {
            ru: "Количество elite-initiated событий по годам.",
            en: "Count of elite-initiated events by year.",
          },
        },
        {
          id: "events_by_period",
          src: "figures/events_by_period.png",
          title: {
            ru: "События по периодам",
            en: "Events by period",
          },
          caption: {
            ru: "Агрегация по историческим периодам.",
            en: "Aggregation by historical period.",
          },
        },
        {
          id: "events_by_domain",
          src: "figures/events_by_domain.png",
          title: {
            ru: "События по decision_domain",
            en: "Events by decision_domain",
          },
          caption: {
            ru: "Расклад по доменам решений.",
            en: "Distribution across decision domains.",
          },
        },
        {
          id: "event_severity_timeline",
          src: "figures/event_severity_timeline.png",
          wide: true,
          title: {
            ru: "Timeline severity",
            en: "Severity timeline",
          },
          caption: {
            ru: "Размер и прозрачность точек зависят от confidence.",
            en: "Point size and opacity depend on confidence.",
          },
        },
      ],
    },
  ];

  const CORRELATION_DEFS = [
    {
      section: "elite",
      items: [
        {
          x: "ruler_age",
          y: "ruler_political_age",
          ru: "Возраст правителя почти линейно связан с политическим возрастом.",
          en: "Ruler age is almost linearly tied to political age.",
        },
        {
          x: "core_mean_age",
          y: "renewal_5y",
          ru: "Чем старше core elite, тем слабее renewal_5y.",
          en: "Older core elite aligns with weaker 5-year renewal.",
        },
        {
          x: "ruler_age",
          y: "core_weighted_mean_age",
          ru: "Возраст правителя сильнее совпадает со взвешенным возрастом core elite, чем с простым средним.",
          en: "Ruler age matches weighted core age more closely than plain mean age.",
        },
      ],
    },
    {
      section: "faction",
      items: [
        {
          x: "normalized_power_share",
          y: "mean_political_age",
          ru: "Более возрастные фракции обычно имеют меньшую normalized_power_share.",
          en: "Older factions usually carry a lower normalized_power_share.",
        },
        {
          x: "raw_power_share",
          y: "members_count",
          ru: "Сырая власть фракции заметно связана с размером группы.",
          en: "Raw faction power tracks group size fairly closely.",
        },
      ],
    },
    {
      section: "event",
      items: [
        {
          x: "elite_initiated_events_count",
          y: "elite_initiated_max_severity",
          ru: "Чем больше elite-initiated событий, тем выше их максимальная severity.",
          en: "More elite-initiated events coincide with higher max severity.",
        },
        {
          x: "renewal_5y",
          y: "elite_initiated_events_count",
          ru: "Обновление элиты связано с большим числом elite-initiated событий.",
          en: "Elite renewal is associated with more elite-initiated events.",
        },
        {
          x: "core_mean_age",
          y: "renewal_5y",
          ru: "Старение core elite идёт вместе со снижением renewal_5y.",
          en: "Aging core elite goes together with lower renewal_5y.",
        },
      ],
    },
  ];

  const VARIABLE_LABELS = {
    ru: {
      ruler_age: "Возраст правителя",
      ruler_political_age: "Политический возраст правителя",
      core_mean_age: "Средний возраст core elite",
      core_weighted_mean_age: "Взвешенный возраст core elite",
      renewal_5y: "Обновление за 5 лет",
      normalized_power_share: "Нормированная доля власти",
      mean_political_age: "Средний политический возраст",
      raw_power_share: "Сырая доля власти",
      members_count: "Число членов",
      elite_initiated_events_count: "Число elite-initiated событий",
      elite_initiated_max_severity: "Макс. severity",
      fragmentation_index: "Индекс фрагментации",
    },
    en: {
      ruler_age: "Ruler age",
      ruler_political_age: "Ruler political age",
      core_mean_age: "Core elite mean age",
      core_weighted_mean_age: "Core elite weighted age",
      renewal_5y: "5-year renewal",
      normalized_power_share: "Normalized power share",
      mean_political_age: "Mean political age",
      raw_power_share: "Raw power share",
      members_count: "Member count",
      elite_initiated_events_count: "Elite-initiated event count",
      elite_initiated_max_severity: "Max severity",
      fragmentation_index: "Fragmentation index",
    },
  };

  const EVENT_TYPE_LABELS = {
    ru: {
      reform: "Реформа",
      repression: "Репрессия",
      war: "Война",
      crisis: "Кризис",
      coup: "Переворот",
      election: "Выборы",
      institutional_change: "Институциональное изменение",
      external_policy: "Внешняя политика",
      constitutional_change: "Конституционное изменение",
      transition: "Переход",
      appointment: "Назначение",
      protest: "Протест",
      economic_shock: "Экономический шок",
      security_operation: "Операция безопасности",
      other: "Другое",
    },
    en: {
      reform: "Reform",
      repression: "Repression",
      war: "War",
      crisis: "Crisis",
      coup: "Coup",
      election: "Election",
      institutional_change: "Institutional change",
      external_policy: "Foreign policy",
      constitutional_change: "Constitutional change",
      transition: "Transition",
      appointment: "Appointment",
      protest: "Protest",
      economic_shock: "Economic shock",
      security_operation: "Security operation",
      other: "Other",
    },
  };

  const INSTITUTION_LABELS = {
    ru: {
      party_state: "Партийно-государственный блок",
      presidential: "Президентский блок",
      government: "Правительство",
      security: "Силовой блок",
      foreign_policy: "Внешняя политика",
      finance: "Финансовый блок",
      military: "Военный блок",
      judiciary: "Судебная система",
      regional: "Региональный уровень",
      administrative: "Административный аппарат",
      central_bank: "Центральный банк",
      legislature: "Законодательный орган",
      other: "Другое",
    },
    en: {
      party_state: "Party-state bloc",
      presidential: "Presidential bloc",
      government: "Government",
      security: "Security bloc",
      foreign_policy: "Foreign policy",
      finance: "Finance bloc",
      military: "Military bloc",
      judiciary: "Judiciary",
      regional: "Regional level",
      administrative: "Administrative apparatus",
      central_bank: "Central bank",
      legislature: "Legislature",
      other: "Other",
    },
  };

  const DIMENSION_LABELS = {
    ru: {
      initiator_group: {
        imp_bureaucratic_reformers: "Имперские бюрократические реформаторы",
        technocrats: "Технократы",
        siloviki: "Силовики",
        rev_bolshevik_center: "Большевистский центр",
        stalin_security_apparatus: "Сталинский аппарат безопасности",
        perestroika_gorbachev_reformers: "Реформаторы Горбачёва",
        central_leader: "Центральный лидер",
        imp_military_aristocracy: "Имперская военная аристократия",
        imp_foreign_policy_chancery: "Имперская внешнеполитическая канцелярия",
        imp_finance_modernizers: "Имперские финансовые модернизаторы",
      },
      decision_domain: {
        foreign_policy_military: "Внешняя политика и военные вопросы",
        economic_policy: "Экономическая политика",
        security: "Безопасность",
        constitutional: "Конституционные вопросы",
        elite_governance: "Управление элитой",
        foreign_policy: "Внешняя политика",
        finance: "Финансы",
        administration: "Администрация",
        military: "Военные вопросы",
        political_institutions: "Политические институты",
      },
      faction_type: {
        functional: "Функциональные",
        bureaucratic_ideological: "Бюрократически-идеологические",
        security: "Силовые",
        personal_power_center: "Личные центры власти",
        party_apparatus: "Партийный аппарат",
        institutional: "Институциональные",
        party_revolutionary: "Партийно-революционные",
        military: "Военные",
        reformist_power_center: "Реформистские центры власти",
        personal_network: "Личные сети",
      },
    },
    en: {
      initiator_group: {
        imp_bureaucratic_reformers: "Imperial bureaucratic reformers",
        technocrats: "Technocrats",
        siloviki: "Siloviki",
        rev_bolshevik_center: "Bolshevik center",
        stalin_security_apparatus: "Stalin security apparatus",
        perestroika_gorbachev_reformers: "Gorbachev reformers",
        central_leader: "Central leader",
        imp_military_aristocracy: "Imperial military aristocracy",
        imp_foreign_policy_chancery: "Imperial foreign policy chancery",
        imp_finance_modernizers: "Imperial finance modernizers",
      },
      decision_domain: {
        foreign_policy_military: "Foreign policy and military",
        economic_policy: "Economic policy",
        security: "Security",
        constitutional: "Constitutional affairs",
        elite_governance: "Elite governance",
        foreign_policy: "Foreign policy",
        finance: "Finance",
        administration: "Administration",
        military: "Military",
        political_institutions: "Political institutions",
      },
      faction_type: {
        functional: "Functional",
        bureaucratic_ideological: "Bureaucratic-ideological",
        security: "Security",
        personal_power_center: "Personal power center",
        party_apparatus: "Party apparatus",
        institutional: "Institutional",
        party_revolutionary: "Party-revolutionary",
        military: "Military",
        reformist_power_center: "Reformist power center",
        personal_network: "Personal network",
      },
    },
  };

  const PERIOD_LABELS = {
    ru: {
      empire_1801_1917: "Российская империя",
      revolution_1917_1924: "Революция и ранний СССР",
      stalin_1924_1953: "Сталинский период",
      poststalin_1953_1964: "Постсталинский период",
      lateussr_1964_1985: "Поздний СССР",
      perestroika_1985_1991: "Перестройка",
      rf_1991_2026: "Российская Федерация",
    },
    en: {
      empire_1801_1917: "Russian Empire",
      revolution_1917_1924: "Revolution / early Soviet",
      stalin_1924_1953: "Stalin era",
      poststalin_1953_1964: "Post-Stalin / Khrushchev",
      lateussr_1964_1985: "Late Soviet",
      perestroika_1985_1991: "Perestroika",
      rf_1991_2026: "Russian Federation",
    },
  };

  function getText(path) {
    return path.split(".").reduce((acc, key) => (acc ? acc[key] : undefined), I18N[state.lang]);
  }

  function formatNumber(value, digits = 2) {
    if (value === null || value === undefined) {
      return "—";
    }
    return new Intl.NumberFormat(state.lang === "ru" ? "ru-RU" : "en-US", {
      maximumFractionDigits: digits,
    }).format(value);
  }

  function formatInteger(value) {
    if (value === null || value === undefined) {
      return "—";
    }
    return new Intl.NumberFormat(state.lang === "ru" ? "ru-RU" : "en-US").format(value);
  }

  function getCorrelation(section, x, y) {
    const matrix = state.data?.correlations?.[section];
    if (!matrix) {
      return null;
    }
    return matrix?.[x]?.[y] ?? matrix?.[y]?.[x] ?? null;
  }

  function render() {
    if (!state.data) {
      return;
    }

    document.documentElement.lang = state.lang;
    document.title = I18N[state.lang].title;

    const meta = state.data.meta;
    document.getElementById("page-title").textContent = I18N[state.lang].title;
    document.getElementById("page-lead").textContent = I18N[state.lang].lead;
    const closeButton = document.querySelector("[data-lightbox-close]");
    if (closeButton) {
      closeButton.textContent = I18N[state.lang].close;
    }

    document.getElementById("meta").innerHTML = [
      badge(`${meta.years.start}–${meta.years.end}`),
      badge(`${formatInteger(meta.counts.persons)} ${I18N[state.lang].meta.persons}`),
      badge(`${formatInteger(meta.counts.events)} ${I18N[state.lang].meta.events}`),
      badge(`${formatInteger(meta.counts.elite_events)} ${I18N[state.lang].meta.eliteEvents}`),
      badge(`${formatInteger(meta.counts.factions)} ${I18N[state.lang].meta.factions}`),
    ].join("");

    document.getElementById("nav").innerHTML = navMarkup();
    document.getElementById("app").innerHTML = appMarkup();
    document.getElementById("footer").innerHTML = I18N[state.lang].footer;

    document.querySelectorAll("[data-lang]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.lang === state.lang));
    });

    document.querySelectorAll("[data-tab]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.tab === state.tab));
    });
  }

  function badge(text) {
    return `<span>${escapeHtml(text)}</span>`;
  }

  function navMarkup() {
    const nav = I18N[state.lang].nav;
    return [
      link("#overview", nav.overview),
      link("#correlations", nav.correlations),
      link("#core", nav.core),
      link("#factions", nav.factions),
      link("#events", nav.events),
      link("#crosstabs", nav.crosstabs),
      link("#notes", nav.notes),
    ].join("");
  }

  function link(href, text) {
    return `<a class="nav-link" href="${href}">${escapeHtml(text)}</a>`;
  }

  function appMarkup() {
    return [
      sectionOverview(),
      sectionCorrelations(),
      sectionFigures("core", "core"),
      sectionFactions(),
      sectionEvents(),
      sectionCrosstabs(),
      sectionNotes(),
    ].join("");
  }

  function sectionOverview() {
    return `
      <section id="overview" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.overview"))}</h2>
          <p class="section-note">${escapeHtml(I18N[state.lang].lead)}</p>
        </div>
        <div class="content">
          <div class="summary-grid">
            ${summaryCard(
              "1801–2026",
              `${formatInteger(state.data.meta.counts.persons)} ${I18N[state.lang].meta.persons}`,
              state.lang === "ru" ? "Диапазон анализа" : "Analysis range"
            )}
            ${summaryCard(
              formatInteger(state.data.meta.counts.elite_events),
              state.lang === "ru" ? "elite-initiated событий" : "elite-initiated events",
              state.lang === "ru" ? "Событийный слой" : "Event layer"
            )}
            ${summaryCard(
              formatInteger(state.data.meta.counts.factions),
              state.lang === "ru" ? "фракций" : "factions",
              state.lang === "ru" ? "Исторический и современный слои" : "Historical and modern layers"
            )}
            ${summaryCard(
              formatInteger(state.data.meta.counts.person_factions),
              state.lang === "ru" ? "привязок" : "links",
              state.lang === "ru" ? "Слой фракционных связей" : "Faction link layer"
            )}
            ${summaryCard(
              formatInteger(state.data.event_summaries?.periods?.length || 0),
              state.lang === "ru" ? "периодов" : "periods",
              state.lang === "ru" ? "Историческая разбивка" : "Historical segmentation"
            )}
          </div>
        </div>
      </section>
    `;
  }

  function summaryCard(value, label, caption) {
    return `
      <div class="summary-card">
        <strong>${escapeHtml(caption)}</strong>
        <div class="value">${escapeHtml(value)}</div>
        <div class="label">${escapeHtml(label)}</div>
      </div>
    `;
  }

  function sectionCorrelations() {
    const insights = state.data.insights || [];
    const correlationCards = CORRELATION_DEFS.map((group) => {
      const items = group.items
        .map((item) => {
          const value = getCorrelation(group.section, item.x, item.y);
          return `
            <div class="correlation-item">
              <strong>${escapeHtml(item[state.lang])}</strong>
              <div class="small-note">${escapeHtml(pairLabel(item.x, item.y))}: r=${escapeHtml(
                formatNumber(value, 3)
              )}</div>
            </div>
          `;
        })
        .join("");

      return `
        <div class="signal-card">
          <strong>${escapeHtml(groupTitle(group.section))}</strong>
          <div class="correlation-list">${items}</div>
        </div>
      `;
    }).join("");

    return `
      <section id="correlations" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.correlations"))}</h2>
          <p class="section-note">
            ${escapeHtml(
              state.lang === "ru"
                ? "Ниже не просто цифры, а короткие выводы из корреляций. Это рабочая интерпретация для текущего MVP, а не финальная историческая модель."
                : "These are short takeaways from the computed correlations. They are working interpretations for the current MVP, not a final historical model."
            )}
          </p>
        </div>
        <div class="content">
          <div class="signal-grid">
            <div class="signal-card">
              <strong>${escapeHtml(
                state.lang === "ru" ? "Основные выводы" : "Core takeaways"
              )}</strong>
              <div class="correlation-list">
                ${insights
                  .map(
                    (insight) => `
                      <div class="correlation-item">
                        ${escapeHtml(insight[state.lang])}
                      </div>
                    `
                  )
                  .join("")}
              </div>
            </div>
            <div class="signal-card">
              <strong>${escapeHtml(
                state.lang === "ru" ? "Интерпретация по слоям" : "Layer interpretations"
              )}</strong>
              <div class="correlation-list">
                ${correlationCards}
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
  }

  function groupTitle(section) {
    if (section === "elite") {
      return state.lang === "ru" ? "Элита" : "Elite";
    }
    if (section === "faction") {
      return state.lang === "ru" ? "Фракции" : "Factions";
    }
    return state.lang === "ru" ? "События" : "Events";
  }

  function pairLabel(x, y) {
    return `${labelFor(x)} ↔ ${labelFor(y)}`;
  }

  function labelFor(key) {
    return VARIABLE_LABELS[state.lang][key] || key;
  }

  function labelForDimension(tab, key) {
    const dimension = tab === "faction_type_x_decision_domain" ? "faction_type" : "initiator_group";
    const labels = DIMENSION_LABELS[state.lang][dimension] || {};
    const fallback = DIMENSION_LABELS[state.lang].decision_domain || {};
    return labels[key] || fallback[key] || key;
  }

  function labelForEventType(key) {
    return EVENT_TYPE_LABELS[state.lang][key] || EVENT_TYPE_LABELS[state.lang].other || key;
  }

  function labelForInstitution(key) {
    return INSTITUTION_LABELS[state.lang][key] || INSTITUTION_LABELS[state.lang].other || key;
  }

  function labelForPeriod(key) {
    return PERIOD_LABELS[state.lang][key] || key;
  }

  function sectionFigures(groupId, sectionId) {
    const group = FIGURE_GROUPS.find((item) => item.id === groupId);
    if (!group) {
      return "";
    }

    return `
      <section id="${sectionId}" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText(`sections.${sectionId}`))}</h2>
          <p class="section-note">${escapeHtml(
            sectionId === "core"
              ? (state.lang === "ru"
                  ? "Нажмите на любую картинку, чтобы открыть увеличенную версию."
                  : "Click any image to open a larger view.")
              : (state.lang === "ru"
                  ? "Все графики из текущего MVP собраны в одном месте для быстрого сравнения."
                  : "All current MVP charts are gathered in one place for quick comparison.")
          )}</p>
        </div>
        <div class="content">
          <div class="figure-grid">
            ${group.figures.map((figure) => renderFigure(figure)).join("")}
          </div>
        </div>
      </section>
    `;
  }

  function sectionFactions() {
    const groups = FIGURE_GROUPS.filter((item) => item.sectionId === "factions");
    return `
      <section id="factions" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.factions"))}</h2>
          <p class="section-note">${escapeHtml(
            state.lang === "ru"
              ? "Фракционный слой включает современный и исторический материал. Для периодов лучше смотреть на форму распределения power share, а не только на отдельные фамилии."
              : "The faction layer combines modern and historical material. For periods, read the shape of the power-share distribution rather than single names alone."
          )}</p>
        </div>
        <div class="content">
          ${groups
            .map(
              (group, index) => `
                <div class="figure-grid" style="margin-top:${index === 0 ? "0" : "14px"};">
                  ${group.figures.map((figure) => renderFigure(figure)).join("")}
                </div>
              `
            )
            .join("")}
        </div>
      </section>
    `;
  }

  function renderFigure(figure) {
    const title = figure.title[state.lang];
    const caption = figure.caption[state.lang];
    const wideClass = figure.wide ? ' class="wide"' : "";
    return `
      <figure id="${escapeHtml(figure.id)}"${wideClass}>
        <button
          class="figure-trigger"
          type="button"
          data-figure-src="${escapeHtml(figure.src)}"
          data-figure-title="${escapeHtml(title)}"
          data-figure-caption="${escapeHtml(caption)}"
        >
          <img src="${escapeHtml(figure.src)}" alt="${escapeHtml(title)}">
        </button>
        <figcaption class="figure-caption">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(caption)}</span>
        </figcaption>
      </figure>
    `;
  }

  function sectionEvents() {
    const periods = state.data.event_summaries?.periods || [];
    const severity = state.data.event_summaries?.top_severity_5 || [];

    return `
      <section id="events" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.events"))}</h2>
          <p class="section-note">${escapeHtml(
            state.lang === "ru"
              ? "События трактуются как elite-initiated решения или реакции элиты на внешний шок. Графики фокусируются на событиях с elite_initiated = true."
              : "Events are treated as elite-initiated decisions or elite reactions to external shocks. The charts focus on events with elite_initiated = true."
          )}</p>
        </div>
        <div class="content">
          <div class="signal-card" style="margin-bottom:14px;">
            <strong>${escapeHtml(I18N[state.lang].eventNavLabel)}</strong>
            <div class="crosstab-toolbar">
              <a class="pill" href="#events_by_year">${escapeHtml(
                state.lang === "ru" ? "По годам" : "By year"
              )}</a>
              <a class="pill" href="#events_by_period">${escapeHtml(
                state.lang === "ru" ? "По периодам" : "By period"
              )}</a>
              <a class="pill" href="#events_by_domain">${escapeHtml(
                state.lang === "ru" ? "По доменам" : "By domain"
              )}</a>
              <a class="pill" href="#event_severity_timeline">${escapeHtml(
                state.lang === "ru" ? "Severity timeline" : "Severity timeline"
              )}</a>
            </div>
          </div>
          <div class="period-grid" style="margin-bottom:14px;">
            ${periods
              .map(
                (period) => `
                  <div class="period-card">
                    <strong>${escapeHtml(period.label)}</strong>
                    <div class="label">${escapeHtml(labelForPeriod(period.period_id))}</div>
                    <div class="value" style="font-size:22px; margin-top:8px;">${formatInteger(
                      period.events_count
                    )}</div>
                    <div class="label">${escapeHtml(
                      state.lang === "ru" ? "событий" : "events"
                    )} · ${escapeHtml(state.lang === "ru" ? "средняя severity" : "mean severity")}: ${formatNumber(
                      period.mean_severity,
                      2
                    )} · ${escapeHtml(state.lang === "ru" ? "max" : "max")}: ${formatInteger(
                      period.max_severity
                    )}</div>
                  </div>
                `
              )
              .join("")}
          </div>
          <div class="figure-grid">
            ${renderFigure(findFigure("events_by_year"))}
            ${renderFigure(findFigure("events_by_period"))}
            ${renderFigure(findFigure("events_by_domain"))}
            ${renderFigure(findFigure("event_severity_timeline"))}
          </div>
          <div class="signal-card" style="margin-top:14px;">
            <strong>${escapeHtml(I18N[state.lang].severityLabel)}</strong>
            <div class="correlation-list">
              ${severity
                .slice(0, 8)
                .map(
                  (item) => `
                    <div class="correlation-item">
                      ${escapeHtml(item.event_name)} <span class="caption-muted">(${escapeHtml(
                        item.event_id
                      )})</span>
                    </div>
                  `
                )
                .join("")}
            </div>
          </div>
        </div>
      </section>
    `;
  }

  function findFigure(id) {
    for (const group of FIGURE_GROUPS) {
      const figure = group.figures.find((item) => item.id === id);
      if (figure) {
        return figure;
      }
    }
    return null;
  }

  function sectionCrosstabs() {
    const lang = state.lang;
    const label = I18N[lang].crosstabLabel[state.tab];
    const description = I18N[lang].crosstabDescription[state.tab];

    return `
      <section id="crosstabs" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.crosstabs"))}</h2>
          <p class="section-note">${escapeHtml(
            lang === "ru"
              ? "Здесь удобно смотреть не одиночные строки, а структуру пересечений. Таблица переключается между инициаторами событий и типами фракций."
              : "This section is for structure, not single rows. The table toggles between event initiators and faction types."
          )}</p>
        </div>
        <div class="content">
          <div class="crosstab-toolbar">
            ${crosstabButton("initiator_group_x_decision_domain", label)}
            ${crosstabButton("faction_type_x_decision_domain", label)}
          </div>
          <p class="table-note">${escapeHtml(description)}</p>
          ${renderCrosstab(state.tab)}
        </div>
      </section>
    `;
  }

  function crosstabButton(tab, activeLabel) {
    return `
      <button class="toggle" type="button" data-tab="${tab}" aria-pressed="${String(
        state.tab === tab
      )}">
        ${escapeHtml(I18N[state.lang].crosstabLabel[tab])}
      </button>
    `;
  }

  function renderCrosstab(tab) {
    const grid = state.data.cross_tabs[tab];
    if (!grid) {
      return "";
    }

    const rows = grid.rows;
    const cols = grid.cols;
    const matrix = grid.matrix;
    const rowTotals = grid.row_totals;
    const colTotals = grid.col_totals;
    const maxValue = Math.max(1, ...matrix.flat());

    const headerCells = [
      `<th></th>`,
      ...cols.map((col) => `<th>${escapeHtml(labelForDimension(tab, col))}</th>`),
      `<th class="total">${escapeHtml(
        state.lang === "ru" ? "Итого" : "Total"
      )}</th>`,
    ].join("");

    const bodyRows = rows
      .map((row, rowIndex) => {
        const cells = matrix[rowIndex]
          .map((value) => {
            const intensity = value / maxValue;
            const bg = `rgba(15, 118, 110, ${0.06 + intensity * 0.68})`;
            const textColor = intensity > 0.54 ? "#fff" : "#16202b";
            return `<td class="heat" style="background:${bg}; color:${textColor};">${value}</td>`;
          })
          .join("");
        return `
          <tr>
            <th>${escapeHtml(labelForDimension(tab, row))}</th>
            ${cells}
            <td class="total">${rowTotals[rowIndex]}</td>
          </tr>
        `;
      })
      .join("");

    const footerCells = [
      `<th class="total">${escapeHtml(state.lang === "ru" ? "Итого" : "Total")}</th>`,
      ...colTotals.map((value) => `<td class="total">${value}</td>`),
      `<td class="total">${colTotals.reduce((sum, value) => sum + value, 0)}</td>`,
    ].join("");

    return `
      <div class="crosstab-table-wrap">
        <table>
          <thead>
            <tr>${headerCells}</tr>
          </thead>
          <tbody>
            ${bodyRows}
          </tbody>
          <tfoot>
            <tr>${footerCells}</tr>
          </tfoot>
        </table>
      </div>
    `;
  }

  function sectionNotes() {
    return `
      <section id="notes" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.notes"))}</h2>
          <p class="section-note">${escapeHtml(
            state.lang === "ru"
              ? "Это MVP, а не академически проверенный датасет. Многие dates approximate, а curated influence intervals нужны для первых графиков и последующей ручной проверки."
              : "This is an MVP, not an academically verified dataset. Many dates are approximate, and curated influence intervals are here to support the first charts and later manual verification."
          )}</p>
        </div>
        <div class="content">
          <div class="signal-card">
            <strong>${escapeHtml(
              state.lang === "ru" ? "Методологические границы" : "Methodological limits"
            )}</strong>
            <div class="correlation-list">
              <div class="correlation-item">
                ${escapeHtml(
                  state.lang === "ru"
                    ? "Поле political_entry_date местами приближено; его лучше уточнять итеративно по источникам."
                    : "The political_entry_date field is approximate in places; it should be tightened iteratively against sources."
                )}
              </div>
              <div class="correlation-item">
                ${escapeHtml(
                  state.lang === "ru"
                    ? "Фракционный слой лучше сравнивать через faction_type, а не напрямую между историческими faction_id."
                    : "The faction layer is better compared through faction_type than directly across historical faction_id values."
                )}
              </div>
              <div class="correlation-item">
                ${escapeHtml(
                  state.lang === "ru"
                    ? "Картинки на странице открываются по клику, чтобы можно было быстро читать подписи и шкалы."
                    : "Charts open on click so labels and axes are easier to read."
                )}
              </div>
              <div class="correlation-item">
                ${escapeHtml(
                  state.lang === "ru"
                    ? `Читабельные лейблы используются для event_type, institution и period_id; например, ${labelForEventType("reform")} / ${labelForInstitution("presidential")} / ${labelForPeriod("rf_1991_2026")}.`
                    : `Readable labels are used for event_type, institution, and period_id; for example, ${labelForEventType("reform")} / ${labelForInstitution("presidential")} / ${labelForPeriod("rf_1991_2026")}.`
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function openLightbox(src, title, caption) {
    const dialog = document.getElementById("lightbox");
    document.getElementById("lightbox-title").textContent = `${I18N[state.lang].lightboxTitle}: ${title}`;
    const image = document.getElementById("lightbox-image");
    image.src = src;
    image.alt = title;
    document.getElementById("lightbox-caption").textContent = caption;
    dialog.setAttribute("aria-hidden", "false");
  }

  function closeLightbox() {
    const dialog = document.getElementById("lightbox");
    dialog.setAttribute("aria-hidden", "true");
    const image = document.getElementById("lightbox-image");
    image.removeAttribute("src");
    image.alt = "";
  }

  document.addEventListener("click", (event) => {
    const langButton = event.target.closest("[data-lang]");
    if (langButton) {
      state.lang = langButton.dataset.lang;
      localStorage.setItem("power_age_lang", state.lang);
      render();
      return;
    }

    const tabButton = event.target.closest("[data-tab]");
    if (tabButton) {
      state.tab = tabButton.dataset.tab;
      render();
      return;
    }

    const figureButton = event.target.closest("[data-figure-src]");
    if (figureButton) {
      openLightbox(
        figureButton.dataset.figureSrc,
        figureButton.dataset.figureTitle,
        figureButton.dataset.figureCaption
      );
      return;
    }

    if (event.target.closest("[data-lightbox-close]") || event.target.id === "lightbox") {
      closeLightbox();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeLightbox();
    }
  });

  function init() {
    fetch(DATA_URL)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load ${DATA_URL}`);
        }
        return response.json();
      })
      .then((json) => {
        state.data = json;
        render();
      })
      .catch((error) => {
        const app = document.getElementById("app");
        app.innerHTML = `<section><div class="content"><strong>Error</strong><p class="section-note">${escapeHtml(
          error.message
        )}</p></div></section>`;
      });
  }

  init();
})();
