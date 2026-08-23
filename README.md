# wsg -- WorkSheet Generator

Malý nástroj příkazové řádky, který ze složek s LaTeXovými úlohami vytváří
pracovní listy připravené k tisku. Každý pracovní list se sází dvakrát: jako
zadání pro studenty a volitelně jako řešení pro vyučujícího.

* jeden příkaz pro celý projekt (`wsg build`) i pro jediný list (`wsg build 3`)
* úlohy se píší v jediném prostředí, které přijímá body, volitelný název,
  označení obtížnosti a volitelné místo na odpověď
* řešení se píše přímo k úloze a do zadání se prostě nevysází
* hlavička je obyčejná šablona `.tex` se zástupnými symboly, takže vzhled listů
  lze změnit bez zásahu do programu
* seznam balíčků a matematická makra jsou dva běžné soubory `.tex` kopírované
  do každého nového projektu, takže je lze rozšiřovat pro každý projekt zvlášť
* `--a5` umístí dvě shodné kopie ve formátu A5 na jeden list A4 a šetří papír
* `--no-answer-space` vysází zadání bez místa na odpověď

Vyžaduje **Python 3.8+** a distribuci TeXu s **pdflatex** (TeX Live, MiKTeX).
Je-li k dispozici `latexmk`, použije se; jinak se `pdflatex` spustí třikrát.

---

## Instalace

Příkaz se instaluje pouze pro aktuálního uživatele, nejsou potřeba práva
správce. Oba instalátory uloží složku programu do proměnné prostředí
`WSG_HOME` a vytvoří malý spouštěč `wsg`, který umístí do `PATH`.

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

**Linux / macOS**

```bash
bash install.sh
```

Poté otevřete nový terminál a ověřte výsledek:

```bash
wsg --help
```

Odinstalace probíhá stejně -- `uninstall.ps1` / `uninstall.sh`. Ani jeden z nich
nemaže samotnou složku programu.

### "wsg is not recognized" po instalaci

Běžící program si drží kopii prostředí, se kterým byl spuštěn, a tuto kopii
předává všemu, co sám spustí. Nová karta -- nebo i nové okno -- terminálu,
který už byl otevřený, tedy stále má staré `PATH`, bez ohledu na nastavení
systému. **Zavřete aplikaci terminálu úplně** (Windows Terminal, VS Code,
editor, ze kterého shell spouštíte) a spusťte ji znovu.

Chcete-li příkaz použít v okně, které je už otevřené, nastavte obě hodnoty
ručně:

```powershell
$env:WSG_HOME = 'C:\cesta\k\Py-Worksheet-Generator'; $env:Path += ";$env:LOCALAPPDATA\Programs\wsg\bin"
```

```bash
source ~/.bashrc
```

Co instalace skutečně provedla, lze ověřit takto:

```powershell
[Environment]::GetEnvironmentVariable('WSG_HOME', 'User')
[Environment]::GetEnvironmentVariable('Path', 'User')
```

---

## Rychlý start

```bash
wsg new "Programování v Pythonu"     # vytvoří složku projektu
cd programovani-v-pythonu
wsg add "Cykly a podmínky"           # vytvoří 01-cykly-a-podminky/
wsg add "Řetězce a pole"             # vytvoří 02-retezce-a-pole/
                                     # ... úlohy se píší do tasks.tex ...
wsg build --move                     # PDF do kořene projektu
```

---

## Struktura projektu

```
programovani-v-pythonu/
├── config.txt                 nastavení projektu (předmět, třída, ...)
├── default-header.tex         kopie šablony, lze ji libovolně upravovat
├── default-packages.tex       balíčky načítané každým pracovním listem
├── default-macros.tex         matematická makra dostupná v úlohách
├── 01-cykly-a-podminky/
│   ├── config.txt             nastavení tohoto pracovního listu
│   ├── tasks.tex              tělo pracovního listu
│   ├── grading.txt            volitelná tabulka hodnocení
│   ├── 01-cykly-a-podminky.pdf
│   └── 01-cykly-a-podminky-solution.pdf
└── 02-retezce-a-pole/
    └── ...
```

Název složky pracovního listu má vždy tvar `<číslo>-<název>`. Číslo určuje
pořadí, soubory PDF se jmenují podle složky.

---

## Příkazy

### `wsg new <název>`

Vytvoří novou složku projektu spolu s kopií souborů `default-header.tex`,
`default-packages.tex` a `default-macros.tex`. Název se použije jak pro složku
(převedený na jednoduchý ASCII slug), tak jako název předmětu.

| volba | význam |
| --- | --- |
| `--dir <složka>` | jiný název složky |
| `--subject <text>` | jiný název předmětu |
| `--school`, `--class`, `--teacher`, `--year` | volitelné údaje do hlavičky |

### `wsg add <název>`

Vytvoří další složku pracovního listu spolu se souborem `config.txt` a se
souborem `tasks.tex`, který obsahuje několik ukázkových úloh.

| volba | význam |
| --- | --- |
| `-p, --project <složka>` | složka projektu (výchozí: nalezena z aktuální složky) |
| `--dir <název>` | název složky bez čísla |
| `--number <n>` | číslo pracovního listu (výchozí: nejbližší volné) |
| `--no-graded` | pracovní list není bodovaný |
| `--no-solution` | nesází se list s řešením |
| `--no-credentials` | bez řádku pro jméno studenta |
| `--grading` | vytvoří i ukázkový soubor `grading.txt` |

### `wsg build [čísla]`

Přeloží celý projekt, nebo jen uvedené pracovní listy -- `wsg build 3`,
`wsg build 2 5-7`.

| volba | význam |
| --- | --- |
| `-p, --project <složka>` | složka projektu (výchozí: nalezena z aktuální složky) |
| `-m, --move` | uloží PDF do kořene projektu místo do složek pracovních listů |
| `--header <soubor>` | pro tento běh použije jinou šablonu hlavičky |
| `--packages <soubor>` | pro tento běh použije jiný seznam balíčků |
| `--macros <soubor>` | pro tento běh použije jiný soubor s makry |
| `--no-solution` | vysází pouze zadání |
| `--no-answer-space` | zadání bez místa na odpověď (volba `answer` se ignoruje) |
| `--a5` | dvě shodné kopie A5 každého listu na jedné stránce A4 |
| `--keep-aux` | ponechá pomocné soubory překladu |
| `-v, --verbose` | vypíše výstup překladu LaTeXu |
| `--open` | otevře vytvořené soubory PDF (nejvýše čtyři, jinak se jen vypíše varování) |

Pomocné soubory vznikají ve složce `wsg-build/` uvnitř složky pracovního listu
a po úspěšném běhu se mažou. Pokud překlad selže, zůstanou zachovány a vypíše
se cesta k logu.

### `wsg list`

Vypíše pracovní listy projektu, jejich čísla a nastavení. Upozorní také na
list, jehož `number` v `config.txt` neodpovídá číslu ve jménu složky.

### `wsg clean`

Smaže složky `wsg-build`; s volbou `--pdf` i vygenerované soubory PDF.

---

## Konfigurační soubory

Oba konfigurační soubory jsou prosté seznamy `klíč = hodnota`. Řádky začínající
znakem `#` nebo `;` jsou komentáře.

### Projekt -- `config.txt`

| klíč | význam |
| --- | --- |
| `subject` | název předmětu, tiskne se do každé hlavičky |
| `school`, `class`, `teacher`, `year` | volitelné; prázdné hodnoty se netisknou |
| `header` | šablona používaná projektem (výchozí `default-header.tex`) |
| `packages` | seznam balíčků projektu (výchozí `default-packages.tex`) |
| `macros` | soubor s makry projektu (výchozí `default-macros.tex`) |
| `language` | `czech` nebo `english`; nastavuje babel a tištěné popisky (výchozí `czech`) |

`teacher` výchozí šablona netiskne, pouze jí ho zpřístupňuje jako
`\wsgTeacher`.

### Pracovní list -- `config.txt`

| klíč | význam |
| --- | --- |
| `number` | číslo tištěné v hlavičce; tímtéž číslem se list vybírá v `wsg build <n>` |
| `title` | název / téma pracovního listu |
| `tasks` | soubor s tělem listu (výchozí `tasks.tex`) |
| `graded` | `yes` -> body u úloh a rámeček pro celkový počet bodů |
| `solution` | `yes` -> vysází se i `-solution.pdf` |
| `credentials` | `yes` -> řádek pro jméno a příjmení v hlavičce |
| `grading` | soubor s tabulkou hodnocení (výchozí `grading.txt`) |
| `header`, `packages`, `macros` | volitelné soubory jen pro tento pracovní list |

Hodnoty se do dokumentu LaTeXu dostanou tak, jak jsou, takže v nich lze
používat LaTeXové značky. Znaky `%`, `&` a `#` se escapují automaticky.

---

## Psaní úloh

Soubor s úlohami obsahuje pouze tělo dokumentu -- žádnou preambuli ani
`\begin{document}`.

```latex
\begin{task}[title=Rozbor kódu, points=3, answer=lines, lines=5]
  Co vypíše následující program?

  \begin{code}[Python]
for i in range(3):
    print(i * i)
\end{code}

  \begin{solution}
    Vypíše čísla 0, 1 a 4, každé na samostatný řádek.
  \end{solution}
\end{task}
```

### Volby prostředí `task`

| klíč | význam |
| --- | --- |
| `title` | volitelný název úlohy |
| `points` | body za úlohu; používá se desetinná tečka (`2.5`) |
| `stars` | obtížnost: `1` vytiskne `*` za číslem úlohy, `2` vytiskne `**` |
| `bloom` | poznámka pro vyučujícího, tiskne se pouze do listu s řešením |
| `answer` | místo ponechané na odpověď: `none` (výchozí), `blank`, `lines`, `dots`, `box`, `grid` |
| `lines` | počet řádků pro `answer=lines` a `answer=dots` (výchozí 4) |
| `space` | výška pro `answer=blank`, `answer=box` a `answer=grid` (výchozí 4cm) |

Místo na odpověď se nesází do listu s řešením a lze je vypnout i v zadání
volbou `wsg build --no-answer-space`; hodí se pro zadání, kde studenti píší
na vlastní papír, nebo pro úsporný tisk.

Úlohy se číslují automaticky. Body se tisknou jen u bodovaného pracovního
listu a jejich součet se doplní do hlavičky.

Volby jsou seznam `klíč=hodnota`, takže hodnotu obsahující čárku je nutné
uzavřít do složených závorek -- `title={Definice, nebo tvrzení?}`. Bez nich se
LaTeX zastaví s chybou `Package keyval Error: nebo tvrzení? undefined`.

Jakmile alespoň jedna úloha pracovního listu obsahuje `stars`, vytiskne se pod
blokem s názvem jednořádková legenda vysvětlující označení. Jakákoli jiná
hodnota `stars` se vytiskne tak, jak je, takže funguje i `stars=+` nebo
`stars=\dag`.

Klíč `bloom` byl přidán kvůli úrovním Bloomovy taxonomie -- drží zamýšlenou
kognitivní úroveň každé úlohy přímo u úlohy, a přitom zůstává studentům
neviditelný:

```latex
\begin{task}[title=Vlastní protipříklad, stars=1, bloom=hodnocení]
```

### Řešení

Vše uvnitř `\begin{solution} ... \end{solution}` se objeví pouze v listu
s řešením. V zadání LaTeX obsah stále zpracuje -- díky tomu uvnitř fungují
výpisy kódu a verbatim materiál -- ale místo vysázení jej zahodí. Místo na
odpověď se do listu s řešením nesází.

### Zdrojový kód

Balíček `listings` je nastaven pro české znaky s diakritikou a pro zvýrazňování
syntaxe. Použijte zkrácené prostředí `code` nebo přímo `lstlisting`:

```latex
\begin{code}[csharp]
public static int Sum(int a, int b) { return a + b; }
\end{code}
```

Rovnou k dispozici jsou: `Python`, `C`, `cpp` (C++), `csharp` (C#), `Java`,
`bash`, `SQL`, `HTML`, `PHP` a vše ostatní, co balíček listings zná.

> `\end{code}` a `\end{lstlisting}` musí začínat na začátku řádku, jinak se
> odsazení projeví jako řádek výpisu navíc.

---

## Tabulka hodnocení

Obsahuje-li složka pracovního listu soubor `grading.txt`, jeho obsah se převede
na dvousloupcovou tabulku a umístí do hlavičky. Každá dvojice `klíč = hodnota`
se stane jedním řádkem; vyhrazený klíč `_header` obsahuje názvy obou sloupců.

```
_header = Body;Známka

18 - 20 = 1
15 - 17 = 2
11 - 14 = 3
 8 - 10 = 4
 0 -  7 = 5
```

Pokud se tabulka tisknout nemá, soubor smažte.

---

## Šablona hlavičky

`default-header.tex` je úplný LaTeXový dokument se zástupnými symboly. Kopie se
vloží do každého nového projektu, takže každý projekt může vypadat jinak.
Šablonu pro jeden běh lze zvolit také volbou `--header`.

| zástupný symbol | nahrazen |
| --- | --- |
| `<<SUBJECT>>` `<<TITLE>>` `<<NUMBER>>` | předmět, název a číslo listu |
| `<<SCHOOL>>` `<<CLASS>>` `<<TEACHER>>` `<<YEAR>>` | volitelné hodnoty, mohou být prázdné |
| `<<LANGUAGE>>` | `czech` / `english` |
| `<<PAPER>>` `<<FONTSIZE>>` `<<MARGIN>>` | nastavení podle formátu papíru (A4 / A5) |
| `<<SOLUTIONS>>` `<<GRADED>>` `<<CREDENTIALS>>` | `true` / `false`, používají je `\ifwsgSolutions` a spol. |
| `<<PACKAGES>>` `<<MACROS>>` | `\input` seznamu balíčků a maker |
| `<<GRADING_TABLE>>` | tabulka sestavená z `grading.txt`, prázdná, pokud soubor chybí |
| `<<CONTENT>>` | tělo pracovního listu |

`<<CONTENT>>` je povinný, vše ostatní lze vynechat. Vygenerovaný dokument se
zapisuje do složky `wsg-build/`, soubor s úlohami se do něj vtahuje pomocí
`\input`, což znamená, že relativní cesty (obrázky!) se vyhodnocují vůči složce
pracovního listu a chyby LaTeXu ukazují na skutečný řádek souboru `tasks.tex`.

---

## Balíčky a makra

Soubory `default-packages.tex` a `default-macros.tex` se kopírují do každého
nového projektu vedle šablony hlavičky a do dokumentu se vtahují zástupnými
symboly `<<PACKAGES>>` a `<<MACROS>>`. Oba soubory procházejí stejným
dosazováním zástupných symbolů jako hlavička, čímž se do seznamu balíčků
dostane jazyk a formát papíru:

```latex
\usepackage[provide=*,<<LANGUAGE>>]{babel}
\usepackage[<<PAPER>>paper,margin=<<MARGIN>>,...]{geometry}
```

**`default-packages.tex`** načítá to, co pracovní list obvykle potřebuje: babel
a `microtype`, `amsmath` / `amssymb` / `amsthm` / `mathtools`, `tikz`
s obvyklými knihovnami a `pgfplots`, `booktabs`, `tabularx`, `enumitem`,
`multicol`, `tcolorbox`, `listings` a jako poslední `hyperref`. Další balíček
přidáte dopsáním jednoho řádku `\usepackage` do kopie uvnitř projektu.

**`default-macros.tex`** obsahuje matematické značení skript z Aplikované
matematiky ([AM-skripta](https://github.com/D4vEOFF/AM-skripta)), takže úlohu
lze ze skript přenést do pracovního listu beze změny:

| skupina | makra |
| --- | --- |
| množiny | `\R \C \N \Q \Z \F`, `\set`, `\powset`, `\sizeof`, `\abs`, `\admid`, `\setcomplement` |
| zobrazení | `\map`, `\dom`, `\image`, `\kernel`, `\Hom` |
| lineární algebra | `\Dim`, `\Span`, `\Kan`, `\REF`, `\RREF`, `\rank`, `\transpose`, `\matrow`, `\matcol`, `\coord`, `\hommat` |
| kódy | `\hweight`, `\hdist`, `\mindist` |
| logika | `\NOT`, `\AND`, `\NAND`, `\OR`, `\NOR`, `\XOR`, `\character` |
| tvrzení | `definition`, `theorem`, `lemma`, `proposition`, `corollary`, `example`, `remark` a jejich hvězdičkové varianty |
| ostatní | `\cmark`, `\xmark`, `\markred`, `\markblue`, `\circled`, `\problem`, `\bigO`, `\floor`, `\ceil` |

Nic, co patří ke vzhledu listu, tam definováno není -- `task`, `solution`,
místo na odpověď i styl stránky zůstávají v šabloně hlavičky.

Jednotlivý pracovní list může používat vlastní soubory prostřednictvím klíčů
`packages` a `macros` ve svém `config.txt` a jeden běh lze přesměrovat volbami
`--packages` / `--macros`.

---

## Režim A5

`wsg build --a5` přeloží pracovní list nejprve na papír A5 a poté umístí každou
stránku dvakrát vedle sebe na list A4 na šířku, s tenkou linkou pro řez
uprostřed. Vytištěním jednoho listu a jeho rozříznutím vzniknou dvě shodné
kopie. Soubory se jmenují `<název>-a5.pdf`.

---

## Struktura programu

```
wsg.py                 vstupní bod (příkaz wsg)
default-header.tex     výchozí šablona pracovního listu
default-packages.tex   výchozí seznam balíčků
default-macros.tex     výchozí matematická makra
wsgen/                 samotný program
├── cli.py             rozhraní příkazové řádky
├── project.py         projekty a pracovní listy na disku
├── config.py          soubory typu klíč = hodnota
├── template.py        zástupné symboly a tabulka hodnocení
├── builder.py         sestavení jednoho pracovního listu
├── latex.py           spouštění latexmk / pdflatex
└── util.py            pomocné funkce
templates/             soubory kopírované do nových projektů
install.ps1 / .sh      instalace
uninstall.ps1 / .sh    odinstalace
```

Používá se pouze standardní knihovna Pythonu, není co instalovat přes `pip`.
