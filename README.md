# Power Age

Минимальный Python-проект для исследования связи между возрастом правящей элиты и историческими событиями на примере России, СССР и РФ в 1801-2026 годах.

Это MVP, а не готовый академический датасет. Его цель - дать воспроизводимую структуру данных, расчеты и первые графики, которые можно расширять и методологически уточнять.

## Идея

Проект разделяет две шкалы возраста:

- `biological_age` - биологический возраст человека на конкретную дату.
- `political_age` - сколько лет человек находится внутри политического контура с момента `political_entry_date`.

Эти переменные не равны друг другу. Человек может быть биологически старым, но политически новым, или наоборот - сравнительно молодым, но давно встроенным в управленческую элиту.

## Данные

Стартовые CSV лежат в `data/raw`:

- `persons.csv` - базовые данные о людях: идентификатор, имя, дата рождения, дата смерти, происхождение.
- `positions.csv` - позиции во власти: период, институт, уровень, вес влияния, флаги `is_ruler` и `is_core_elite`.
- `political_entries.csv` - даты входа в политику, элиту и правящий круг.
- `events.csv` - исторические события: дата, тип, тяжесть, направление решения.
- `core_elite_groups.csv` - исследовательские правила отбора core elite по периодам.
- `sources_elite_addendum.csv` - навигационные источники для расширенного elite seed dataset.
- `core_elite_groups_early.csv` - правила отбора для Российской империи, 1917 года, раннего СССР, сталинского и хрущевского периодов.
- `sources_early_elite_addendum.csv` - источники для раннего elite seed dataset.

Многие значения `political_entry_date`, `elite_entry_date` и `ruling_circle_entry_date` в стартовом файле приблизительные и требуют ручной проверки.

## Установка

```bash
cd power_age_project
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Запуск

Построить годовую таблицу:

```bash
python -m power_age.cli build
```

Результат сохраняется в `data/processed/elite_year.csv`.

Построить графики:

```bash
python -m power_age.cli plot
```

PNG-файлы сохраняются в `outputs/figures`.

Сейчас строятся:

- `ruler_age_timeline.png` - возраст правителя и события;
- `biological_vs_political_age.png` - биологический и политический возраст правителя;
- `core_elite_age.png` - средний и взвешенный средний возраст core elite;
- `core_elite_aging_dashboard.png` - dashboard: возраст, доли 60+/70+, renewal 5y, размер выборки;
- `ruler_vs_core_age.png` - возраст правителя против среднего возраста core elite;
- `institution_composition.png` - институциональный состав core elite по доле `influence_weight`;
- `period_age_boxplots.png` - распределение возраста core elite по периодам из `core_elite_groups.csv`.

## Графики

### Возраст правителя и события

![Возраст правителя и события](outputs/figures/ruler_age_timeline.png)

### Биологический и политический возраст правителя

![Биологический и политический возраст правителя](outputs/figures/biological_vs_political_age.png)

### Средний возраст core elite

![Средний возраст core elite](outputs/figures/core_elite_age.png)

### Core elite aging dashboard

![Core elite aging dashboard](outputs/figures/core_elite_aging_dashboard.png)

### Возраст правителя против core elite

![Возраст правителя против core elite](outputs/figures/ruler_vs_core_age.png)

### Институциональный состав core elite

![Институциональный состав core elite](outputs/figures/institution_composition.png)

### Возраст core elite по периодам

![Возраст core elite по периодам](outputs/figures/period_age_boxplots.png)

Вывести краткую сводку:

```bash
python -m power_age.cli summary
```

## Тесты

```bash
pytest
```

## GitHub Pages

Для публикации статической версии:

1. Закоммить изменения и отправь репозиторий на GitHub.
2. Открой `Settings -> Pages`.
3. В `Build and deployment` выбери `Deploy from a branch`.
4. В `Branch` выбери `main` и папку `/docs`.
5. Сохрани настройки.

После публикации GitHub Pages будет показывать сайт из `docs/index.html`.

Если графики были перегенерированы, обнови копии для Pages:

```bash
cp outputs/figures/*.png docs/figures/
```

## Elite Addendum

Проект подключен к двум стартовым аддон-датасетам:

- `power_age_early_elite_addendum` - Российская империя, 1917 год, ранний СССР, сталинский и хрущевский периоды.
- `power_age_elite_addendum` - поздний СССР и РФ.

Они расширяют базовые CSV людьми из министерской бюрократии, двора, Политбюро, Совмина, силового блока, администрации президента, Совбеза, правительства, МИД, ЦБ и других частей ядра власти.

Скрипт подключения лежит в `scripts/append_elite_addendum.py`:

```bash
python scripts/append_early_elite_addendum.py ../power_age_early_elite_addendum --project-dir .
python scripts/append_elite_addendum.py ../power_age_elite_addendum
```

Аддон использует curated influence intervals: строка в `positions.csv` означает не каждую формальную должность отдельно, а период, когда человек считается частью реального ядра власти для MVP-расчетов.

## Что уже считается

- возраст правителя на 1 июля каждого года;
- политический, элитный и ruling-circle возраст правителя;
- должностной возраст правителя;
- численность core elite;
- средний, медианный и взвешенный средний возраст core elite;
- доля core elite старше 60 и 70 лет;
- стандартное отклонение возраста;
- `renewal_5y` - доля core elite, вошедших в элиту за последние 5 лет;
- сводка событий по годам.

## Методологические ограничения

В стартовом MVP `core elite` определяется простым флагом в `positions.csv`. Для Российской империи, СССР и РФ реальный состав элиты должен определяться по разным институциональным правилам: монархический двор и министры, партийные органы, политбюро, Совбез, администрация президента, правительство и другие группы требуют отдельных критериев.
