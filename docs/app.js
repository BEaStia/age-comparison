(() => {
  const state = {
    lang: localStorage.getItem("power_age_lang") || "ru",
    tab: "initiator_group_x_decision_domain",
    datasetId: localStorage.getItem("power_age_dataset") || "",
    datasets: [],
    dataset: null,
    data: null,
    series: null,
  };

  const DATASETS_URL = "data/datasets.json";
  const SERIES_URL = "data/series-data.json";
  const FALLBACK_DATASET = {
    id: "russia",
    label: { ru: "Россия / СССР", en: "Russia / USSR" },
    description: {
      ru: "Текущий набор данных по возрасту элиты, фракциям и событиям для России и СССР.",
      en: "Current dataset covering elite age, factions, and events for Russia and the USSR.",
    },
    data_url: "data/site-data.json",
    series_url: "data/series-data.json",
    figures_url: "figures",
  };

  const I18N = {
    ru: {
      title: "Power Age",
      lead:
        "Исследовательский прототип о возрасте элиты, фракциях и событиях. Страница собирает графики, корреляционные выводы, кросс-табы и событийный слой в одном месте.",
      nav: {
        overview: "Обзор",
        correlations: "Корреляции",
        guidance: "Модель",
        forecasts: "Прогнозы",
        interactive: "Интерактив",
        core: "Элита",
        factions: "Фракции",
        events: "События",
        crosstabs: "Кросс-табы",
        notes: "Примечания",
      },
      sections: {
        overview: "Обзор",
        correlations: "Выводы по корреляциям",
        guidance: "Рекомендация модели",
        forecasts: "Прогнозные сигналы",
        interactive: "Интерактивные графики",
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
        initiator_group_x_decision_domain: "Группы инициаторов и домены решений",
        faction_type_x_decision_domain: "Типы фракций и домены решений",
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
        "A research prototype on elite age, factions, and events. The page brings charts, correlation takeaways, cross-tabs, and the event layer into one place.",
      nav: {
        overview: "Overview",
        correlations: "Correlations",
        guidance: "Model",
        forecasts: "Forecasts",
        interactive: "Interactive",
        core: "Elite",
        factions: "Factions",
        events: "Events",
        crosstabs: "Cross-tabs",
        notes: "Notes",
      },
      sections: {
        overview: "Overview",
        correlations: "Correlation takeaways",
        guidance: "Model recommendation",
        forecasts: "Forecast signals",
        interactive: "Interactive charts",
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
        initiator_group_x_decision_domain: "Initiator groups and decision domains",
        faction_type_x_decision_domain: "Faction types and decision domains",
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
            ru: "Средний возраст, 60+/70+, обновление за 5 лет и размер ядра власти.",
            en: "Mean age, 60+/70+, 5-year renewal, and core size.",
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
            ru: "Stacked area chart по нормированной доле власти.",
            en: "Stacked area chart of normalized power share.",
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
            ru: "1 минус сумма квадратов нормированной доли власти.",
            en: "1 minus the sum of squared normalized power shares.",
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
            ru: "Год x фракция по нормированной доле власти.",
            en: "Year by faction heatmap of normalized power share.",
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
          datasets: ["russia"],
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
            ru: "События по доменам решений",
            en: "Events by decision domains",
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
          ru: "Чем старше core elite, тем слабее обновление за 5 лет.",
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
          ru: "Более возрастные фракции обычно имеют меньшую нормированную долю власти.",
          en: "Older factions usually carry a lower normalized power share.",
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
          ru: "Старение core elite идёт вместе со снижением обновления за 5 лет.",
          en: "Aging core elite goes together with lower 5-year renewal.",
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

  const PERIOD_LABELS = {
    ru: {
      empire_1801_1917: "Российская империя",
      revolution_1917_1924: "Революция и ранний СССР",
      stalin_1924_1953: "Сталинский период",
      poststalin_1953_1964: "Постсталинский период",
      lateussr_1964_1985: "Поздний СССР",
      perestroika_1985_1991: "Перестройка",
      rf_1991_2026: "Российская Федерация",
      other: "Другое",
    },
    en: {
      empire_1801_1917: "Russian Empire",
      revolution_1917_1924: "Revolution / early Soviet",
      stalin_1924_1953: "Stalin era",
      poststalin_1953_1964: "Post-Stalin / Khrushchev",
      lateussr_1964_1985: "Late Soviet",
      perestroika_1985_1991: "Perestroika",
      rf_1991_2026: "Russian Federation",
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
    document.getElementById("controls").innerHTML = renderControls();
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
    renderD3Charts();

    document.querySelectorAll("[data-lang]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.lang === state.lang));
    });

    document.querySelectorAll("[data-tab]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.tab === state.tab));
    });

    document.querySelectorAll("[data-dataset]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.dataset === state.datasetId));
    });
  }

  function renderControls() {
    const dataset = state.dataset || FALLBACK_DATASET;
    const datasetLabel = dataset.label?.[state.lang] || dataset.label?.ru || dataset.id;
    const options = state.datasets.length
      ? state.datasets
      : [FALLBACK_DATASET];
    const datasetButtons = options
      .map(
        (item) => `
          <button class="toggle" type="button" data-dataset="${escapeHtml(item.id)}" aria-pressed="${String(
            item.id === state.datasetId
          )}">${escapeHtml(item.label?.[state.lang] || item.label?.ru || item.id)}</button>
        `
      )
      .join("");

    return `
      <div class="controls-block">
        <div class="controls-group">
          <span class="pill">${escapeHtml(datasetLabel)}</span>
          ${datasetButtons}
        </div>
        <div class="controls-group">
          <button class="toggle" type="button" data-lang="ru" aria-pressed="${String(
            state.lang === "ru"
          )}">RU</button>
          <button class="toggle" type="button" data-lang="en" aria-pressed="${String(
            state.lang === "en"
          )}">EN</button>
        </div>
      </div>
    `;
  }

  function badge(text) {
    return `<span>${escapeHtml(text)}</span>`;
  }

  function navMarkup() {
    const nav = I18N[state.lang].nav;
    return [
      link("#overview", nav.overview),
      link("#correlations", nav.correlations),
      link("#guidance", nav.guidance),
      link("#forecasts", nav.forecasts),
      link("#interactive", nav.interactive),
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
      sectionModelGuidance(),
      sectionForecasts(),
      sectionInteractiveCharts(),
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
      const items = getCorrelationItems(group.section, group.items)
        .map((item) => {
          const value = getCorrelation(group.section, item.x, item.y);
          if (value === null || value === undefined) {
            return null;
          }
          return `
            <div class="correlation-item">
              <strong>${escapeHtml(item[state.lang])}</strong>
              <div class="small-note">${escapeHtml(pairLabel(item.x, item.y))}: r=${escapeHtml(
                formatNumber(value, 3)
              )}</div>
            </div>
          `;
        })
        .filter(Boolean)
        .join("");

      if (!items) {
        return null;
      }

      return `
        <div class="signal-card">
          <strong>${escapeHtml(groupTitle(group.section))}</strong>
          <div class="correlation-list">${items}</div>
        </div>
      `;
    }).filter(Boolean).join("");

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

  function sectionModelGuidance() {
    const guidance = state.data?.model_guidance || {};
    const selection = guidance.selection || {};
    const forecast = guidance.forecast || {};
    const family = guidance.selected_family || {};
    const supportingSignals = Array.isArray(selection.supporting_signals) ? selection.supporting_signals : [];
    const missingWarnings = Array.isArray(selection.missing_data_warnings) ? selection.missing_data_warnings : [];
    const nextFeatures = Array.isArray(selection.recommended_next_features) ? selection.recommended_next_features : [];
    const forecastWarnings = Array.isArray(forecast.warnings) ? forecast.warnings : [];
    const localizedSupportingSignals = state.lang === "ru"
      ? (Array.isArray(selection.supporting_signals_ru) ? selection.supporting_signals_ru : supportingSignals)
      : (Array.isArray(selection.supporting_signals_en) ? selection.supporting_signals_en : supportingSignals);
    const localizedMissingWarnings = state.lang === "ru"
      ? (Array.isArray(selection.missing_data_warnings_ru) ? selection.missing_data_warnings_ru : missingWarnings)
      : (Array.isArray(selection.missing_data_warnings_en) ? selection.missing_data_warnings_en : missingWarnings);
    const localizedNextFeatures = state.lang === "ru"
      ? (Array.isArray(selection.recommended_next_features_ru) ? selection.recommended_next_features_ru : nextFeatures)
      : (Array.isArray(selection.recommended_next_features_en) ? selection.recommended_next_features_en : nextFeatures);
    const localizedForecastWarnings = state.lang === "ru"
      ? (Array.isArray(forecast.warnings_ru) ? forecast.warnings_ru : forecastWarnings)
      : (Array.isArray(forecast.warnings_en) ? forecast.warnings_en : forecastWarnings);
    const localizedRationale = state.lang === "ru"
      ? (selection.rationale_ru || selection.rationale || "")
      : (selection.rationale_en || selection.rationale || "");

    const modelLabel = labelForModelFamily(
      family.model_id || selection.recommended_model,
      family.label || selection.recommended_model || "model"
    );
    const confidence = selection.confidence == null ? "n/a" : formatNumber(Number(selection.confidence), 2);
    const localizedForecastType = state.lang === "ru"
      ? forecast.forecast_type_ru || forecast.forecast_type || "сценарный"
      : forecast.forecast_type_en || forecast.forecast_type || "scenario";
    const localizedTarget = state.lang === "ru"
      ? forecast.target_ru || forecast.target || "n/a"
      : forecast.target_en || forecast.target || "n/a";
    const localizedBaseline = state.lang === "ru"
      ? forecast.baseline_assessment_ru || forecast.baseline_assessment || ""
      : forecast.baseline_assessment_en || forecast.baseline_assessment || ""
    ;
    const localizedUpside = state.lang === "ru"
      ? forecast.upside_scenario_ru || forecast.upside_scenario || ""
      : forecast.upside_scenario_en || forecast.upside_scenario || "";
    const localizedDownside = state.lang === "ru"
      ? forecast.downside_scenario_ru || forecast.downside_scenario || ""
      : forecast.downside_scenario_en || forecast.downside_scenario || "";
    const upsideLabel = state.lang === "ru" ? "Позитивный сценарий" : "Upside";
    const downsideLabel = state.lang === "ru" ? "Негативный сценарий" : "Downside";
    const whyNotAgeOnlyLabel = state.lang === "ru" ? "Почему age-only модель слабее" : "Why not age-only";
    const dataLimitsLabel = state.lang === "ru" ? "Ограничения данных" : "Data limitations";
    const whatToAddLabel = state.lang === "ru" ? "Что добавить в следующий проход" : "What to add next";
    const watchLabel = state.lang === "ru" ? "Наблюдать" : "Watch";

    return `
      <section id="guidance" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.guidance"))}</h2>
          <p class="section-note">
            ${escapeHtml(
              state.lang === "ru"
                ? "Этот блок отделяет описательную историю от корреляции и от сценарного прогноза. Он показывает, какая модель лучше подходит для данного страны-периода и почему."
                : "This block separates descriptive history from correlation and scenario forecast. It shows which model fits the current country-period best and why."
            )}
          </p>
        </div>
        <div class="content">
          <div class="signal-grid">
            <div class="signal-card">
              <strong>${escapeHtml(
                state.lang === "ru" ? "Рекомендуемая модель" : "Recommended model"
              )}</strong>
              <div class="correlation-list">
                <div class="correlation-item">
                  <strong>${escapeHtml(selection.recommended_model || "n/a")}</strong>
                  <div class="small-note">
                    ${escapeHtml(
                      state.lang === "ru"
                        ? `Семейство: ${modelLabel}`
                        : `Family: ${modelLabel}`
                    )}
                  </div>
                  <div class="small-note">
                    ${escapeHtml(
                      state.lang === "ru"
                        ? `Уверенность: ${confidence}`
                        : `Confidence: ${confidence}`
                    )}
                  </div>
                  <div class="small-note">
                    ${escapeHtml(localizedRationale || (state.lang === "ru" ? "Рационализация основана на priors и наблюдаемых сигналах." : "Rationale is based on priors and observed signals."))}
                  </div>
                </div>
              </div>
            </div>
            <div class="signal-card">
              <strong>${escapeHtml(whyNotAgeOnlyLabel)}</strong>
              <div class="correlation-list">
                ${(localizedSupportingSignals.length ? localizedSupportingSignals : [state.lang === "ru" ? "Сигналы пока недостаточно специфичны." : "Signals are still too sparse."])
                  .map(
                    (signal) => `
                      <div class="correlation-item">${escapeHtml(signal)}</div>
                    `
                  )
                  .join("")}
              </div>
              ${localizedMissingWarnings.length ? `<div class="small-note" style="margin-top:10px;">${escapeHtml(dataLimitsLabel)}</div>` : ""}
              <div class="correlation-list">
                ${localizedMissingWarnings
                  .map((warning) => `<div class="correlation-item">${escapeHtml(warning)}</div>`)
                  .join("")}
              </div>
            </div>
            <div class="signal-card">
              <strong>${escapeHtml(
                state.lang === "ru" ? "Сценарный прогноз" : "Scenario forecast"
              )}</strong>
              <div class="correlation-list">
                <div class="correlation-item">
                  <div><strong>${escapeHtml(localizedForecastType)}</strong></div>
                  <div class="small-note">
                    ${escapeHtml(
                      state.lang === "ru"
                        ? `Горизонт: ${forecast.forecast_horizon_years || "n/a"} лет`
                        : `Horizon: ${forecast.forecast_horizon_years || "n/a"} years`
                    )}
                  </div>
                  <div class="small-note">
                    ${escapeHtml(
                      state.lang === "ru"
                        ? `Цель: ${localizedTarget}`
                        : `Target: ${localizedTarget}`
                    )}
                  </div>
                  <div class="small-note">${escapeHtml(localizedBaseline)}</div>
                  <div class="small-note" style="margin-top:8px;">
                    <strong>${escapeHtml(upsideLabel)}</strong>
                    ${escapeHtml(localizedUpside)}
                  </div>
                  <div class="small-note" style="margin-top:8px;">
                    <strong>${escapeHtml(downsideLabel)}</strong>
                    ${escapeHtml(localizedDownside)}
                  </div>
                </div>
                <div class="correlation-item">
                  <strong>${escapeHtml(watchLabel)}</strong>
                  <div class="small-note">
                    ${escapeHtml(
                      (state.lang === "ru"
                        ? (forecast.key_indicators_to_watch_ru || forecast.key_indicators_to_watch || [])
                        : (forecast.key_indicators_to_watch_en || forecast.key_indicators_to_watch || []))
                        .map((item) => labelForForecastIndicator(item))
                        .join(", ") || (state.lang === "ru" ? "Сигналы еще не заданы." : "Indicators are not yet set.")
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div class="signal-card">
              <strong>${escapeHtml(whatToAddLabel)}</strong>
              <div class="correlation-list">
                ${(localizedNextFeatures.length ? localizedNextFeatures : [state.lang === "ru" ? "Дополнительные признаки не определены." : "No additional features are defined."])
                  .map(
                    (feature) => `
                      <div class="correlation-item">${escapeHtml(feature)}</div>
                    `
                  )
                  .join("")}
              </div>
              <div class="small-note" style="margin-top:10px;">
                ${escapeHtml(
                  state.lang === "ru"
                    ? "Это не детерминистический прогноз. Он сценарный и ограничен качеством доступных данных."
                    : "This is not a deterministic forecast. It is scenario-based and bounded by data quality."
                )}
              </div>
              <div class="small-note" style="margin-top:10px;">
                ${escapeHtml(
                  state.lang === "ru"
                    ? "Любые сигналы, не подтвержденные несколькими независимыми слоями, следует считать слабой гипотезой, а не выводом."
                    : "Any signal not confirmed by multiple independent layers should be treated as a weak hypothesis, not a conclusion."
                )}
              </div>
              ${localizedForecastWarnings.length ? `<div class="correlation-list" style="margin-top:10px;">${localizedForecastWarnings.map((warning) => `<div class="correlation-item">${escapeHtml(warning)}</div>`).join("")}</div>` : ""}
            </div>
          </div>
        </div>
      </section>
    `;
  }

  function sectionForecasts() {
    const forecasts = buildForecastSignals();
    return `
      <section id="forecasts" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.forecasts"))}</h2>
          <p class="section-note">
            ${escapeHtml(
              state.lang === "ru"
                ? "Это сценарные прогнозы, а не точные предсказания. Они показывают, какие траектории логично проверять дальше."
                : "These are scenario forecasts, not exact predictions. They show which trajectories are most worth testing next."
            )}
          </p>
        </div>
        <div class="content">
          <div class="signal-grid">
            <div class="signal-card">
              <strong>${escapeHtml(
                state.lang === "ru" ? "Что смотреть дальше" : "What to watch next"
              )}</strong>
              <div class="small-note" style="margin-top:8px;">
                ${escapeHtml(
                  state.lang === "ru"
                    ? "Это не точные предсказания. Это сценарии, которые логично проверять следующими, если текущие связи сохраняются."
                    : "These are not exact predictions. They are scenarios worth testing next if the current links hold."
                )}
              </div>
              <div class="correlation-list">
                ${forecasts
                  .map(
                    (item) => `
                      <div class="correlation-item">
                        <strong>${escapeHtml(item.title[state.lang])}</strong>
                        <div class="small-note">${escapeHtml(
                          state.lang === "ru"
                            ? `Уверенность: ${item.confidence.ru}`
                            : `Confidence: ${item.confidence.en}`
                        )}</div>
                        <div class="small-note">${escapeHtml(item.evidence[state.lang])}</div>
                        <div class="small-note">${escapeHtml(item.body[state.lang])}</div>
                      </div>
                    `
                  )
                  .join("")}
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
  }

  function sectionInteractiveCharts() {
    return `
      <section id="interactive" class="section-anchor">
        <div class="section-head">
          <h2>${escapeHtml(getText("sections.interactive"))}</h2>
          <p class="section-note">
            ${escapeHtml(
              state.lang === "ru"
                ? "Интерактивные версии строятся через D3. Тут меньше шума, больше осей, подсказок и читаемости."
                : "Interactive versions are rendered with D3. They reduce clutter and make axes and tooltips easier to read."
            )}
          </p>
        </div>
        <div class="content">
          <div class="chart-grid">
            <div class="chart-shell chart-shell--wide" id="d3-ruler-chart-shell">
              <div class="chart-head">
                <strong>${escapeHtml(
                  state.lang === "ru" ? "Возраст правителя и события" : "Ruler age and events"
                )}</strong>
                <p>${escapeHtml(
                  state.lang === "ru"
                    ? "События показаны точками с подсказками; по оси X шаг 5 лет."
                    : "Events are shown as points with tooltips; the X axis uses 5-year steps."
                )}</p>
              </div>
              <div class="chart-body" id="d3-ruler-chart"></div>
            </div>
            <div class="chart-shell chart-shell--wide" id="d3-severity-chart-shell">
              <div class="chart-head">
                <strong>${escapeHtml(
                  state.lang === "ru" ? "Severity timeline событий" : "Event severity timeline"
                )}</strong>
                <p>${escapeHtml(
                  state.lang === "ru"
                    ? "Размер точки отражает confidence, подписи убраны из поля графика."
                    : "Point size reflects confidence, and labels are kept out of the plotting area."
                )}</p>
              </div>
              <div class="chart-body" id="d3-severity-chart"></div>
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

  function getCorrelationItems(section, items) {
    if (section !== "event") {
      return items;
    }

    const eventMatrix = state.data?.correlations?.event;
    if (eventMatrix && Object.keys(eventMatrix).length) {
      return items;
    }

    return [
      {
        x: "events_count",
        y: "elite_initiated_events_count",
        ru: "Чем больше событий в целом, тем больше elite-initiated событий.",
        en: "More total events coincide with more elite-initiated events.",
      },
      {
        x: "core_mean_age",
        y: "elite_initiated_events_count",
        ru: "Возраст core elite слабо связан с числом elite-initiated событий.",
        en: "Core elite age is only weakly related to elite-initiated event volume.",
      },
      {
        x: "renewal_5y",
        y: "elite_initiated_events_count",
        ru: "Обновление за 5 лет связано с числом elite-initiated событий.",
        en: "5-year renewal is linked with elite-initiated event volume.",
      },
    ];
  }

  function labelFor(key) {
    return VARIABLE_LABELS[state.lang][key] || key;
  }

  function labelForModelFamily(modelId, fallback) {
    if (state.lang !== "ru") {
      return fallback || modelId;
    }
    const labels = {
      institutional_domain_crisis_model: "институциональная / доменная / кризисная модель",
      gerontocracy_succession_model: "геронтократическая / преемственная модель",
      dynastic_succession_model: "династическая модель преемственности",
      party_congress_turnover_model: "модель съездов и обновления",
      revolutionary_generation_model: "модель революционного поколения",
      security_state_faction_model: "модель силового государства и фракций",
      developmental_bureaucratic_model: "модель бюрократического развития",
    };
    return labels[modelId] || fallback || modelId;
  }

  function labelForForecastIndicator(value) {
    if (state.lang !== "ru") {
      return value;
    }
    const labels = {
      security_elite_share: "доля силовой элиты",
      faction_concentration: "концентрация фракций",
      recent_purge_or_repression_events: "недавние чистки или подавление",
      war_or_external_pressure: "война или внешнее давление",
      turnover_decline: "снижение обновления элиты",
      major_crisis: "крупный кризис",
      divided_government: "разделенное управление",
      high_severity_event_rate: "частота событий высокой severity",
      natsec_elite_share: "доля национально-безопасностной элиты",
      finance_elite_share: "доля финансовой элиты",
      judicial_elite_share: "доля судебной элиты",
    };
    if (labels[value]) {
      return labels[value];
    }
    const normalized = String(value)
      .replaceAll("_", " ")
      .toLowerCase();
    const fallback = {
      "security elite share": "доля силовой элиты",
      "faction concentration": "концентрация фракций",
      "recent purge or repression events": "недавние чистки или подавление",
      "war or external pressure": "война или внешнее давление",
      "turnover decline": "снижение обновления элиты",
      "major crisis": "крупный кризис",
      "divided government": "разделенное управление",
      "high severity event rate": "частота событий высокой severity",
      "natsec elite share": "доля национально-безопасностной элиты",
      "finance elite share": "доля финансовой элиты",
      "judicial elite share": "доля судебной элиты",
    };
    return fallback[normalized] || String(value);
  }

  function labelForDimension(tab, key) {
    const dimension = tab === "faction_type_x_decision_domain" ? "faction_type" : "initiator_group";
    const labels = DIMENSION_LABELS[state.lang][dimension] || {};
    const fallback = DIMENSION_LABELS[state.lang].decision_domain || {};
    return labels[key] || fallback[key] || prettifyKey(key);
  }

  function labelForEventType(key) {
    return EVENT_TYPE_LABELS[state.lang][key] || EVENT_TYPE_LABELS[state.lang].other || key;
  }

  function labelForInstitution(key) {
    return INSTITUTION_LABELS[state.lang][key] || INSTITUTION_LABELS[state.lang].other || key;
  }

  function labelForPeriod(key) {
    const periods = Array.isArray(state.data?.periods) ? state.data.periods : [];
    const match = periods.find((period) => period.period_id === key || period.slug === key);
    if (match) {
      return match[`label_${state.lang}`] || match.label || match.label_en || match.label_ru || key;
    }
    return PERIOD_LABELS[state.lang][key] || key;
  }

  function examplePeriodKey() {
    const periods = Array.isArray(state.data?.periods) ? state.data.periods : [];
    const first = periods[0] || {};
    return first.period_id || first.slug || "period";
  }

  function buildForecastSignals() {
    const modelGuidance = state.data?.model_guidance || null;
    const elite = state.data?.correlations?.elite || {};
    const faction = state.data?.correlations?.faction || {};
    const event = state.data?.correlations?.event || {};
    const signals = [];

    if (modelGuidance?.selection && modelGuidance?.forecast) {
      const selection = modelGuidance.selection;
      const forecast = modelGuidance.forecast;
      const family = modelGuidance.selected_family || {};
      const confidenceValue = Number(selection.confidence || 0);
      signals.push({
        title: {
          ru: "Рекомендуемая модель",
          en: "Recommended model",
        },
        body: {
          ru:
            `Для этого периода рекомендуемая модель: ${selection.recommended_model}. ` +
            `${forecast.baseline_assessment || ""}` +
            (family.label ? ` Это соответствует семейству: ${labelForModelFamily(family.model_id || selection.recommended_model, family.label)}.` : ""),
          en:
            `Recommended model for this period: ${selection.recommended_model}. ` +
            `${forecast.baseline_assessment || ""}` +
            (family.label ? ` This maps to the family: ${family.label}.` : ""),
        },
        evidence: {
          ru:
            `Уверенность: ${formatNumber(confidenceValue, 2)}. ` +
            (selection.rationale ? `Причина: ${selection.rationale}` : "Причина задана данными и priors."),
          en:
            `Confidence: ${formatNumber(confidenceValue, 2)}. ` +
            (selection.rationale ? `Reason: ${selection.rationale}` : "Reason is driven by data and priors."),
        },
        confidence: forecastConfidence(confidenceValue),
      });
    }

    const rulerPolitical = elite?.ruler_age?.ruler_political_age ?? null;
    const coreRenewal = elite?.core_mean_age?.renewal_5y ?? null;
    const rulerWeightedCore = elite?.ruler_age?.core_weighted_mean_age ?? null;
    const coreEvents =
      elite?.core_mean_age?.elite_initiated_events_count ??
      event?.core_mean_age?.elite_initiated_events_count ??
      null;
    const eventVolume =
      elite?.events_count?.elite_initiated_events_count ??
      event?.events_count?.elite_initiated_events_count ??
      null;
    const factionPower = faction?.normalized_power_share?.raw_power_share ?? null;
    const factionConcentration = faction?.normalized_power_share?.members_count ?? null;
    const eventRenewal =
      event?.renewal_5y?.elite_initiated_events_count ??
      elite?.renewal_5y?.elite_initiated_events_count ??
      null;
    const eventSeverity = event?.elite_initiated_events_count?.elite_initiated_max_severity ?? null;
    const turbulenceSignal = eventSeverity ?? eventVolume ?? eventRenewal;

    return signals.concat([
      {
        title: {
          ru: "Обновление элиты",
          en: "Elite renewal",
        },
        body: {
          ru:
            coreRenewal === null
              ? "Связь между возрастом core elite и обновлением кадров пока слишком шумная для уверенного сценария."
              : Math.abs(coreRenewal) >= 0.4
                ? `Если текущая связь сохранится, старение ядра власти будет и дальше означать более медленное обновление кадров. Сейчас r=${formatNumber(
                    coreRenewal,
                    3
                  )}.`
                : `Старение ядра власти связано с обновлением кадров, но сигнал умеренный. Его стоит читать вместе с институциональным составом. Сейчас r=${formatNumber(
                    coreRenewal,
                    3
                  )}.`,
          en:
            coreRenewal === null
              ? "The link between core age and turnover is still too noisy for a confident scenario."
              : Math.abs(coreRenewal) >= 0.4
                ? `If the current relation holds, an older core elite will keep implying slower turnover. Current r=${formatNumber(
                    coreRenewal,
                    3
                  )}.`
                : `Core aging is linked with turnover, but the signal is moderate. It should be read together with institutional composition. Current r=${formatNumber(
                    coreRenewal,
                    3
                  )}.`,
        },
        evidence: {
          ru:
            coreRenewal === null
              ? "Опорная связь пока нестабильна."
              : `Опорная связь: ${labelFor("core_mean_age")} ↔ ${labelFor("renewal_5y")} (r=${formatNumber(coreRenewal, 3)}).`,
          en:
            coreRenewal === null
              ? "The anchor link is still unstable."
              : `Anchor link: ${labelFor("core_mean_age")} ↔ ${labelFor("renewal_5y")} (r=${formatNumber(coreRenewal, 3)}).`,
        },
        confidence: forecastConfidence(coreRenewal),
      },
      {
        title: {
          ru: "Смена лидера",
          en: "Leadership transition",
        },
        body: {
          ru:
            rulerWeightedCore === null || rulerPolitical === null
              ? "Связь между правителем и ядром элиты требует дальнейшей проверки."
              : Math.abs(rulerWeightedCore) >= 0.7
                ? `Смена первого лица, скорее всего, будет воспроизводить возрастной профиль системы: правитель сильно связан со взвешенным возрастом core elite (r=${formatNumber(
                    rulerWeightedCore,
                    3
                  )}).`
                : `Смена первого лица может частично отражать возрастной профиль системы, но связь умеренная: возраст правителя ↔ взвешенный возраст core elite r=${formatNumber(
                    rulerWeightedCore,
                    3
                  )}, возраст правителя ↔ политический возраст r=${formatNumber(rulerPolitical, 3)}.`,
          en:
            rulerWeightedCore === null || rulerPolitical === null
              ? "The ruler-to-elite link still needs more checking."
              : Math.abs(rulerWeightedCore) >= 0.7
                ? `Leadership change will likely preserve the system's age profile: ruler age is strongly tied to weighted core age (r=${formatNumber(
                    rulerWeightedCore,
                    3
                  )}).`
                : `Leadership change may partly reflect the system's age profile, but the link is moderate: ruler age ↔ weighted core age r=${formatNumber(
                    rulerWeightedCore,
                    3
                  )}, ruler age ↔ political age r=${formatNumber(rulerPolitical, 3)}.`,
        },
        evidence: {
          ru:
            rulerWeightedCore === null
              ? "Опорная связь пока слабая."
              : `Опорная связь: ${labelFor("ruler_age")} ↔ ${labelFor("core_weighted_mean_age")} (r=${formatNumber(
                  rulerWeightedCore,
                  3
                )}).`,
          en:
            rulerWeightedCore === null
              ? "The anchor link is still weak."
              : `Anchor link: ${labelFor("ruler_age")} ↔ ${labelFor("core_weighted_mean_age")} (r=${formatNumber(
                  rulerWeightedCore,
                  3
                )}).`,
        },
        confidence: forecastConfidence(rulerWeightedCore),
      },
      {
        title: {
          ru: "Событийное давление",
          en: "Event pressure",
        },
        body: {
          ru:
            coreEvents === null
              ? "Возраст сам по себе пока не даёт достаточно сигнала о будущих всплесках событий."
              : Math.abs(coreEvents) < 0.2
                ? `Возраст ядра власти сам по себе слабо предсказывает всплески событий. Для следующего цикла важнее следить за составом институтов и доменами решений. Связь с elite-initiated событиями сейчас r=${formatNumber(
                    coreEvents,
                    3
                  )}${eventVolume === null ? "." : `, а связь общего числа событий с elite-initiated событиями r=${formatNumber(eventVolume, 3)}.`}`
                : `Возраст ядра власти даёт заметный событийный сигнал: связь с elite-initiated событиями сейчас r=${formatNumber(
                    coreEvents,
                    3
                  )}.`,
          en:
            coreEvents === null
              ? "Age alone still does not give enough signal about future event spikes."
              : Math.abs(coreEvents) < 0.2
                ? `Core age by itself is a weak predictor of event spikes. The next cycle should be read through institutional composition and decision domains. The current link with elite-initiated events is r=${formatNumber(
                    coreEvents,
                    3
                  )}${eventVolume === null ? "." : `, while total events and elite-initiated events correlate at r=${formatNumber(eventVolume, 3)}.`}`
                : `Core age gives a visible event signal: the current link with elite-initiated events is r=${formatNumber(
                    coreEvents,
                    3
                  )}.`,
        },
        evidence: {
          ru:
            coreEvents === null
              ? "Опорная связь пока отсутствует."
              : `Опорная связь: ${labelFor("core_mean_age")} ↔ ${labelFor("elite_initiated_events_count")} (r=${formatNumber(
                  coreEvents,
                  3
                )}).`,
          en:
            coreEvents === null
              ? "The anchor link is still missing."
              : `Anchor link: ${labelFor("core_mean_age")} ↔ ${labelFor("elite_initiated_events_count")} (r=${formatNumber(
                  coreEvents,
                  3
                )}).`,
        },
        confidence: forecastConfidence(coreEvents),
      },
      {
        title: {
          ru: "Баланс фракций",
          en: "Faction balance",
        },
        body: {
          ru:
            factionPower === null || factionConcentration === null
              ? "Фракционный баланс пока лучше читать как исследовательский сценарий."
              : `Когда доля власти концентрируется у нескольких групп, будущие сдвиги будут чаще выглядеть как перекройка коалиций, а не как широкое распыление власти. В текущих корреляциях нормированная доля власти особенно тесно связана с сырой долей власти (r=${formatNumber(
                  factionPower,
                  3
                )}) и размером группы (r=${formatNumber(factionConcentration, 3)}).`,
          en:
            factionPower === null || factionConcentration === null
              ? "Faction balance is still best read as a research scenario."
              : `When power share concentrates in a few groups, future shifts are more likely to look like coalition reshuffling than broad dispersion. In the current correlations, normalized power share is tightly linked to raw power share (r=${formatNumber(
                  factionPower,
                  3
                )}) and group size (r=${formatNumber(factionConcentration, 3)}).`,
        },
        evidence: {
          ru:
            factionPower === null
              ? "Опорная связь пока нестабильна."
              : `Опорная связь: ${labelFor("normalized_power_share")} ↔ ${labelFor("raw_power_share")} (r=${formatNumber(
                  factionPower,
                  3
                )}).`,
          en:
            factionPower === null
              ? "The anchor link is still unstable."
              : `Anchor link: ${labelFor("normalized_power_share")} ↔ ${labelFor("raw_power_share")} (r=${formatNumber(
                  factionPower,
                  3
                )}).`,
        },
        confidence: forecastConfidence(factionPower),
      },
      {
        title: {
          ru: "Окно высокой турбулентности",
          en: "High-turbulence window",
        },
        body: {
          ru:
            turbulenceSignal === null
              ? "Турбулентность пока лучше читать по периодам, а не как линейный тренд."
              : eventSeverity !== null
                ? `Следующий стресс-сценарий стоит искать в периодах, где elite-initiated события усиливаются вместе с максимальной severity. Сейчас число elite-initiated событий ↔ максимальная severity равно r=${formatNumber(
                    eventSeverity,
                    3
                  )}.`
                : `Для этого датасета главный событийный сигнал не в возрасте, а в плотности событийного слоя: общее число событий ↔ число elite-initiated событий равно r=${formatNumber(
                    turbulenceSignal,
                    3
                  )}.`,
          en:
            turbulenceSignal === null
              ? "Turbulence is still better read by periods than as a linear trend."
              : eventSeverity !== null
                ? `The next stress scenario should be searched for in periods where elite-initiated events rise together with max severity. Right now elite-initiated event count ↔ max severity is r=${formatNumber(
                    eventSeverity,
                    3
                  )}.`
                : `For this dataset, the main event signal is not age but event-layer density: total events ↔ elite-initiated event count is r=${formatNumber(
                    turbulenceSignal,
                    3
                  )}.`,
        },
        evidence: {
          ru:
            turbulenceSignal === null
              ? "Сигнал пока неустойчив."
              : eventSeverity !== null
                ? `Опорная связь: ${labelFor("elite_initiated_events_count")} ↔ ${labelFor("elite_initiated_max_severity")} (r=${formatNumber(eventSeverity, 3)}).`
                : `Опорная связь: число событий ↔ ${labelFor("elite_initiated_events_count")} (r=${formatNumber(turbulenceSignal, 3)}).`,
          en:
            turbulenceSignal === null
              ? "The signal is still unstable."
              : eventSeverity !== null
                ? `Anchor link: ${labelFor("elite_initiated_events_count")} ↔ ${labelFor("elite_initiated_max_severity")} (r=${formatNumber(eventSeverity, 3)}).`
                : `Anchor link: total event count ↔ ${labelFor("elite_initiated_events_count")} (r=${formatNumber(turbulenceSignal, 3)}).`,
        },
        confidence: forecastConfidence(turbulenceSignal),
      },
    ]);
  }

  function forecastConfidence(value) {
    const magnitude = Math.abs(Number(value) || 0);
    if (magnitude >= 0.4) {
      return { ru: "высокая", en: "high" };
    }
    if (magnitude >= 0.2) {
      return { ru: "средняя", en: "medium" };
    }
    return { ru: "низкая", en: "low" };
  }

  function isVisibleForDataset(entry) {
    return !entry.datasets || entry.datasets.includes(state.datasetId);
  }

  function figureAssetPath(src) {
    const prefix = (state.dataset?.figures_url || FALLBACK_DATASET.figures_url || "figures").replace(/\/$/, "");
    const normalized = String(src).replace(/^figures\//, "");
    return `${prefix}/${normalized}`;
  }

  function prettifyKey(key) {
    return String(key)
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function sectionFigures(groupId, sectionId) {
    const group = FIGURE_GROUPS.find((item) => item.id === groupId);
    if (!group || !isVisibleForDataset(group)) {
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
    const groups = FIGURE_GROUPS.filter((item) => item.sectionId === "factions" && isVisibleForDataset(item));
    if (!groups.length) {
      return "";
    }
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
    const src = figureAssetPath(figure.src);
    const wideClass = figure.wide ? ' class="wide"' : "";
    return `
      <figure id="${escapeHtml(figure.id)}"${wideClass}>
        <button
          class="figure-trigger"
          type="button"
          data-figure-src="${escapeHtml(src)}"
          data-figure-title="${escapeHtml(title)}"
          data-figure-caption="${escapeHtml(caption)}"
        >
          <img src="${escapeHtml(src)}" alt="${escapeHtml(title)}">
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
                    <strong>${escapeHtml(period.label || period.period_label || period.period_id)}</strong>
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
                    ? "Поле даты политического входа местами приближено; его лучше уточнять итеративно по источникам."
                    : "The political-entry date is approximate in places; it should be tightened iteratively against sources."
                )}
              </div>
              <div class="correlation-item">
                ${escapeHtml(
                  state.lang === "ru"
                    ? "Фракционный слой лучше сравнивать через тип фракции, а не напрямую между историческими идентификаторами фракций."
                    : "The faction layer is better compared through faction type than directly across historical faction identifiers."
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
                    ? `Читабельные лейблы используются для типа события, института и периода; например, ${labelForEventType("reform")} / ${labelForInstitution("presidential")} / ${labelForPeriod(examplePeriodKey())}.`
                    : `Readable labels are used for event type, institution, and period; for example, ${labelForEventType("reform")} / ${labelForInstitution("presidential")} / ${labelForPeriod(examplePeriodKey())}.`
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    `;
  }

  function renderD3Charts() {
    const shellRuler = document.getElementById("d3-ruler-chart");
    const shellSeverity = document.getElementById("d3-severity-chart");
    if (!shellRuler || !shellSeverity) {
      return;
    }

    if (!window.d3 || !state.series) {
      const fallbackHtml = `
        <div class="chart-fallback">
          ${escapeHtml(
            state.lang === "ru"
              ? "Интерактивный слой D3 недоступен, поэтому используйте PNG-версию графика ниже."
              : "The D3 layer is unavailable, so use the PNG version below."
          )}
        </div>
      `;
      shellRuler.innerHTML = fallbackHtml;
      shellSeverity.innerHTML = fallbackHtml;
      return;
    }

    renderRulerAgeChart(shellRuler, state.series.elite_year || [], state.series.events || []);
    renderEventSeverityChart(shellSeverity, state.series.events || []);
  }

  function createChartTooltip(shell) {
    const tooltip = document.createElement("div");
    tooltip.className = "chart-tooltip";
    shell.appendChild(tooltip);
    return tooltip;
  }

  function showTooltip(tooltip, shell, event, html) {
    const rect = shell.getBoundingClientRect();
    const offsetX = event.clientX - rect.left + 14;
    const offsetY = event.clientY - rect.top + 14;
    tooltip.innerHTML = html;
    tooltip.style.left = `${Math.min(offsetX, rect.width - 300)}px`;
    tooltip.style.top = `${Math.min(offsetY, rect.height - 120)}px`;
    tooltip.style.opacity = "1";
  }

  function hideTooltip(tooltip) {
    tooltip.style.opacity = "0";
  }

  function renderRulerAgeChart(shell, eliteYear, events) {
    const d3 = window.d3;
    shell.innerHTML = "";
    const width = Math.max(960, shell.getBoundingClientRect().width - 20);
    const height = 420;
    const margin = { top: 20, right: 18, bottom: 72, left: 58 };
    const svg = d3
      .select(shell)
      .append("svg")
      .attr("class", "chart-svg")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    const tooltip = createChartTooltip(shell);

    const years = eliteYear.map((d) => +d.year).filter((d) => Number.isFinite(d));
    if (!years.length) {
      shell.innerHTML = `<div class="chart-fallback">${escapeHtml(
        state.lang === "ru" ? "Нет данных для интерактивного графика." : "No data for the interactive chart."
      )}</div>`;
      return;
    }

    const x = d3
      .scaleLinear()
      .domain(d3.extent(years))
      .range([margin.left, width - margin.right]);

    const rulerValues = eliteYear.map((d) => +d.ruler_age).filter((d) => Number.isFinite(d));
    const y = d3
      .scaleLinear()
      .domain([d3.min(rulerValues) - 2, d3.max(rulerValues) + 2])
      .nice()
      .range([height - margin.bottom, margin.top]);

    const line = d3
      .line()
      .defined((d) => Number.isFinite(d.ruler_age))
      .x((d) => x(+d.year))
      .y((d) => y(+d.ruler_age));

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(
        d3
          .axisBottom(x)
          .tickValues(d3.range(d3.min(years), d3.max(years) + 1, 5))
          .tickFormat(d3.format("d"))
      )
      .call((g) => g.selectAll("text").attr("transform", "rotate(45)").attr("text-anchor", "start"))
      .call((g) => g.select(".domain").attr("stroke", "#9fb0be"));

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(6))
      .call((g) => g.select(".domain").attr("stroke", "#9fb0be"));

    svg
      .append("path")
      .datum(eliteYear)
      .attr("fill", "none")
      .attr("stroke", "#0f766e")
      .attr("stroke-width", 2.4)
      .attr("d", line);

    const eventData = events
      .filter((d) => d.elite_initiated && Number.isFinite(d.year))
      .map((d) => ({ ...d, ruler_age: eliteYear.find((row) => +row.year === +d.year)?.ruler_age }))
      .filter((d) => Number.isFinite(+d.ruler_age));

    svg
      .append("g")
      .selectAll("circle")
      .data(eventData)
      .join("circle")
      .attr("cx", (d) => x(+d.year))
      .attr("cy", (d) => y(+d.ruler_age))
      .attr("r", (d) => 3 + Math.max(0, +d.severity || 0) * 0.9)
      .attr("fill", (d) => (d.severity >= 5 ? "#b33a3a" : "#d76666"))
      .attr("fill-opacity", (d) => Math.min(0.9, 0.45 + (d.confidence || 0) * 0.45))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1)
      .on("mouseenter", function (event, d) {
        d3.select(this).attr("stroke", "#0f766e").attr("stroke-width", 2);
        showTooltip(
          tooltip,
          shell,
          event,
          `
            <strong>${escapeHtml(d.event_name || "")}</strong>
            <div>${escapeHtml(String(d.date || d.year || ""))}</div>
            <div>${escapeHtml(
              state.lang === "ru"
                ? `Severity: ${d.severity ?? "—"}`
                : `Severity: ${d.severity ?? "—"}`
            )}</div>
            <div>${escapeHtml(
              state.lang === "ru"
                ? `Возраст правителя: ${formatNumber(d.ruler_age, 1)}`
                : `Ruler age: ${formatNumber(d.ruler_age, 1)}`
            )}</div>
            <div>${escapeHtml(
              state.lang === "ru"
                ? `Домен: ${labelForDimension(state.tab, d.decision_domain || "")}`
                : `Domain: ${labelForDimension(state.tab, d.decision_domain || "")}`
            )}</div>
          `
        );
      })
      .on("mousemove", (event) => {
        const current = tooltip.innerHTML;
        if (current) {
          showTooltip(tooltip, shell, event, current);
        }
      })
      .on("mouseleave", function () {
        d3.select(this).attr("stroke", "#fff").attr("stroke-width", 1);
        hideTooltip(tooltip);
      });

    svg
      .append("text")
      .attr("x", margin.left)
      .attr("y", height - 18)
      .attr("fill", "#5b6775")
      .attr("font-size", 12)
      .text(state.lang === "ru" ? "Год" : "Year");

    svg
      .append("text")
      .attr("x", 14)
      .attr("y", margin.top + 8)
      .attr("fill", "#5b6775")
      .attr("font-size", 12)
      .text(state.lang === "ru" ? "Возраст правителя" : "Ruler age");
  }

  function renderEventSeverityChart(shell, events) {
    const d3 = window.d3;
    shell.innerHTML = "";
    const width = Math.max(960, shell.getBoundingClientRect().width - 20);
    const height = 420;
    const margin = { top: 20, right: 18, bottom: 72, left: 58 };
    const svg = d3
      .select(shell)
      .append("svg")
      .attr("class", "chart-svg")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    const tooltip = createChartTooltip(shell);
    const data = events.filter((d) => d.elite_initiated && Number.isFinite(d.year) && Number.isFinite(+d.severity));
    if (!data.length) {
      shell.innerHTML = `<div class="chart-fallback">${escapeHtml(
        state.lang === "ru" ? "Нет данных для интерактивного графика." : "No data for the interactive chart."
      )}</div>`;
      return;
    }

    const years = data.map((d) => +d.year);
    const x = d3
      .scaleLinear()
      .domain(d3.extent(years))
      .range([margin.left, width - margin.right]);
    const y = d3.scaleLinear().domain([0.5, 5.5]).range([height - margin.bottom, margin.top]);
    const r = d3.scaleSqrt().domain([0, 1]).range([3, 10]);

    svg
      .append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(
        d3
          .axisBottom(x)
          .tickValues(d3.range(d3.min(years), d3.max(years) + 1, 5))
          .tickFormat(d3.format("d"))
      )
      .call((g) => g.selectAll("text").attr("transform", "rotate(45)").attr("text-anchor", "start"))
      .call((g) => g.select(".domain").attr("stroke", "#9fb0be"));

    svg
      .append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y).ticks(5))
      .call((g) => g.select(".domain").attr("stroke", "#9fb0be"));

    svg.append("g")
      .selectAll("line.grid")
      .data(d3.range(1, 6))
      .join("line")
      .attr("x1", margin.left)
      .attr("x2", width - margin.right)
      .attr("y1", (d) => y(d))
      .attr("y2", (d) => y(d))
      .attr("stroke", "#e4e9ef")
      .attr("stroke-dasharray", "2,2");

    svg
      .append("g")
      .selectAll("circle")
      .data(data)
      .join("circle")
      .attr("cx", (d) => x(+d.year))
      .attr("cy", (d) => y(+d.severity))
      .attr("r", (d) => r(Math.min(1, Math.max(0, +d.confidence || 0))))
      .attr("fill", (d) => (d.severity >= 5 ? "#b33a3a" : "#6f4e9b"))
      .attr("fill-opacity", (d) => Math.min(0.95, 0.35 + (d.confidence || 0) * 0.55))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1)
      .on("mouseenter", function (event, d) {
        d3.select(this).attr("stroke", "#0f766e").attr("stroke-width", 2);
        showTooltip(
          tooltip,
          shell,
          event,
          `
            <strong>${escapeHtml(d.event_name || "")}</strong>
            <div>${escapeHtml(String(d.date || d.year || ""))}</div>
            <div>${escapeHtml(
              state.lang === "ru"
                ? `Severity: ${d.severity ?? "—"}`
                : `Severity: ${d.severity ?? "—"}`
            )}</div>
            <div>${escapeHtml(
              state.lang === "ru"
                ? `Confidence: ${formatNumber(d.confidence, 2)}`
                : `Confidence: ${formatNumber(d.confidence, 2)}`
            )}</div>
            <div>${escapeHtml(
              state.lang === "ru"
                ? `Тип: ${labelForEventType(d.event_type || "")}`
                : `Type: ${labelForEventType(d.event_type || "")}`
            )}</div>
          `
        );
      })
      .on("mousemove", (event) => {
        const current = tooltip.innerHTML;
        if (current) {
          showTooltip(tooltip, shell, event, current);
        }
      })
      .on("mouseleave", function () {
        d3.select(this).attr("stroke", "#fff").attr("stroke-width", 1);
        hideTooltip(tooltip);
      });

    svg
      .append("text")
      .attr("x", margin.left)
      .attr("y", height - 18)
      .attr("fill", "#5b6775")
      .attr("font-size", 12)
      .text(state.lang === "ru" ? "Год" : "Year");

    svg
      .append("text")
      .attr("x", 14)
      .attr("y", margin.top + 8)
      .attr("fill", "#5b6775")
      .attr("font-size", 12)
      .text(state.lang === "ru" ? "Severity" : "Severity");
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
    const scrollTarget = event.target.closest("[data-scroll-target]");
    if (scrollTarget) {
      event.preventDefault();
      const targetId = scrollTarget.dataset.scrollTarget;
      const target = targetId ? document.getElementById(targetId) : null;
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        history.replaceState(null, "", `#${targetId}`);
      }
      return;
    }

    const langButton = event.target.closest("[data-lang]");
    if (langButton) {
      state.lang = langButton.dataset.lang;
      localStorage.setItem("power_age_lang", state.lang);
      render();
      return;
    }

    const datasetButton = event.target.closest("[data-dataset]");
    if (datasetButton) {
      state.datasetId = datasetButton.dataset.dataset;
      localStorage.setItem("power_age_dataset", state.datasetId);
      init();
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
    fetch(DATASETS_URL)
      .then((response) => (response.ok ? response.json() : [FALLBACK_DATASET]))
      .catch(() => [FALLBACK_DATASET])
      .then((datasets) => {
        state.datasets = Array.isArray(datasets) ? datasets : [FALLBACK_DATASET];
        const selected =
          state.datasets.find((item) => item.id === state.datasetId) || state.datasets[0] || FALLBACK_DATASET;
        state.datasetId = selected.id;
        localStorage.setItem("power_age_dataset", state.datasetId);
        return Promise.all([
          fetch(selected.data_url)
            .then((response) => {
              if (!response.ok) {
                throw new Error(`Failed to load ${selected.data_url}`);
              }
              return response.json();
            })
            .catch(() => fetch(FALLBACK_DATASET.data_url).then((response) => response.json())),
          fetch(selected.series_url || SERIES_URL)
            .then((response) => {
              if (!response.ok) {
                throw new Error(`Failed to load ${selected.series_url || SERIES_URL}`);
              }
              return response.json();
            })
            .catch(() => null),
        ]);
      })
      .then(([data, series]) => {
        state.data = data;
        state.series = series;
        state.dataset = state.datasets.find((item) => item.id === state.datasetId) || FALLBACK_DATASET;
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
