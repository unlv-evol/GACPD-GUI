#include "headers/FileInterface.h"
#include "headers/CodeEditor.h"

#include <QPlainTextEdit>
#include <QSplitter>
#include <QFileDialog>
#include <QFile>
#include <QTextStream>
#include <QMenuBar>
#include <QMenu>
#include <QAction>
#include <QMessageBox>
#include <QFontDatabase>
#include <QInputDialog>
#include <QTextBlock>
#include <QTextCursor>
#include <QBrush>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFileInfo>
#include <QTimer>
#include <QComboBox>
#include <QGroupBox>
#include <QLabel>
#include <QFrame>
#include <QDir>
#include <QDirIterator>
#include <QSet>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>

// =================== Fixed root holder (constructor provides) ===================
static QString kRootDir = QStringLiteral("C:/PATH/TO/YOUR/root"); // overwritten by ctor arg

// ---------- globals ----------
static QString g_rootDir; // assigned from kRootDir at startup
static QMap<QString, QSet<QString> > g_class_to_prs; // Classification -> {PRs}
static QHash<QString, QString> g_srcToHunk;          // src file -> hunk name

// ---------- helpers ----------
static QString canonicalOrOriginal(const QString &p) {
    QFileInfo fi(p);
    const QString c = fi.canonicalFilePath();
    return c.isEmpty() ? p : c;
}

static bool isPatch(const QString &path) {
    return path.endsWith(".patch", Qt::CaseInsensitive);
}

// Parse "<PR>_<Classification>" → (PR, Classification). Use the last '_' as the split.
static bool parsePRClass(const QString &folderName, QString &outPR, QString &outClass) {
    int lastUnderscore = folderName.lastIndexOf('_');
    if (lastUnderscore <= 0 || lastUnderscore >= folderName.size() - 1)
        return false;
    outPR = folderName.left(lastUnderscore);
    outClass = folderName.mid(lastUnderscore + 1);
    return !outPR.isEmpty() && !outClass.isEmpty();
}

static void scanRootForPRsAndClasses(const QString &rootPath) {
    g_class_to_prs.clear();
    QDir root(rootPath);
    if (!root.exists()) return;

    const QList<QFileInfo> entries =
        root.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name);
    for (int i = 0; i < entries.size(); ++i) {
        const QFileInfo &fi = entries.at(i);
        QString pr; QString cls;
        if (parsePRClass(fi.fileName(), pr, cls)) {
            g_class_to_prs[cls].insert(pr);
        }
    }
}

static QStringList sortedSet(const QSet<QString> &set) {
    QStringList list = set.values();
    list.sort(Qt::CaseInsensitive);
    return list;
}

static QString prClassAbsDir(const QString &root, const QString &pr, const QString &cls) {
    return QDir(root).filePath(pr + "_" + cls);
}

// Build a friendly relative label (from base) for a file
static QString relativeLabelFromBase(const QString &baseAbs, const QString &fileAbs) {
    QDir baseDir(baseAbs);
    QString rel = baseDir.relativeFilePath(fileAbs);
#ifdef Q_OS_WIN
    rel.replace('\\', '/');
#endif
    if (rel.isEmpty()) {
        QFileInfo fi(fileAbs);
        rel = fi.fileName();
    }
    return rel;
}

// ---------------- SCANNERS ----------------

// Given an absolute src file, compute the matching repo base (…/<Hunk>/<Github_Path>)
static bool repoBaseFromSrcFile(const QString &srcFileAbs, QString &outRepoBaseAbs) {
    QString norm = srcFileAbs;
#ifdef Q_OS_WIN
    norm.replace('\\', '/');
#endif
    int pos = norm.indexOf("/src/");
    if (pos < 0) {
        pos = norm.lastIndexOf("/src");
        if (pos < 0) return false;
    }
    outRepoBaseAbs = norm.left(pos); // up to .../<Hunk>/<Github_Path>
    return !outRepoBaseAbs.isEmpty();
}

// Given an absolute cmp file, compute the matching repo base (…/<Hunk>/<Github_Path>)
static bool repoBaseFromCmpFile(const QString &cmpFileAbs, QString &outRepoBaseAbs) {
    QString norm = cmpFileAbs;
#ifdef Q_OS_WIN
    norm.replace('\\', '/');
#endif
    int pos = norm.indexOf("/cmp/");
    if (pos < 0) {
        pos = norm.lastIndexOf("/cmp");
        if (pos < 0) return false;
    }
    outRepoBaseAbs = norm.left(pos); // up to .../<Hunk>/<Github_Path>
    return !outRepoBaseAbs.isEmpty();
}

// Scan ALL files under a specific src base (repoBaseAbs + "/src")
static QStringList scanSrcFilesUnderRepo(const QString &repoBaseAbs) {
    QStringList out;
    const QString srcAbs = QDir(repoBaseAbs).filePath("src");
    QDir srcDir(srcAbs);
    if (!srcDir.exists()) return out;

    QDirIterator it(srcAbs, QDir::Files, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        QString f = canonicalOrOriginal(it.next());
        if (isPatch(f)) continue;
        out << f;
    }
    out.sort(Qt::CaseInsensitive);
    return out;
}

// Scan ALL files under a specific cmp base (repoBaseAbs + "/cmp")
static QStringList scanCmpFilesUnderRepo(const QString &repoBaseAbs) {
    QStringList out;
    const QString cmpAbs = QDir(repoBaseAbs).filePath("cmp");
    QDir cmpDir(cmpAbs);
    if (!cmpDir.exists()) return out;

    QDirIterator it(cmpAbs, QDir::Files, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        QString f = canonicalOrOriginal(it.next());
        if (isPatch(f)) continue;
        out << f;
    }
    out.sort(Qt::CaseInsensitive);
    return out;
}

// Scan ALL cmp files across a PR/Class (all repos, all hunks)
static QStringList scanAllCmpFilesForPRClass(const QString &root, const QString &pr, const QString &cls) {
    QStringList out;

    const QString base = prClassAbsDir(root, pr, cls);
    QDir baseDir(base);
    if (!baseDir.exists()) return out;

    const QList<QFileInfo> hunks =
        baseDir.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name);
    for (int hi = 0; hi < hunks.size(); ++hi) {
        const QFileInfo &hunkFi = hunks.at(hi);
        QDir hunkDir(hunkFi.absoluteFilePath());
        const QList<QFileInfo> repos =
            hunkDir.entryInfoList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name);
        for (int ri = 0; ri < repos.size(); ++ri) {
            const QFileInfo &repoFi = repos.at(ri);
            const QString cmpAbs = QDir(repoFi.absoluteFilePath()).filePath("cmp");
            QDir cmpDir(cmpAbs);
            if (!cmpDir.exists()) continue;

            QDirIterator it(cmpAbs, QDir::Files, QDirIterator::Subdirectories);
            while (it.hasNext()) {
                QString f = canonicalOrOriginal(it.next());
                if (isPatch(f)) continue;
                out << f;
            }
        }
    }
    out.sort(Qt::CaseInsensitive);
    return out;
}

// Simple check: is childAbs inside parentAbs?
static bool isUnder(const QString &parentAbs, const QString &childAbs) {
    QDir parent(parentAbs);
    const QString rel = parent.relativeFilePath(childAbs);
    return !rel.startsWith("..");
}

// Populate a file selector with files; tries to keep previous selection
static void refillSelectorKeepSelection(QComboBox *selector,
                                        const QStringList &files,
                                        const QString &baseAbs)
{
    selector->blockSignals(true);
    QString prev = selector->currentData(Qt::UserRole).toString();
    selector->clear();

    for (int i = 0; i < files.size(); ++i) {
        const QString &path = files.at(i);
        QString label = relativeLabelFromBase(baseAbs, path);
        selector->addItem(label, path);
        int idx = selector->count() - 1;
        selector->setItemData(idx, path, Qt::ToolTipRole);
    }

    int newIndex = -1;
    if (!prev.isEmpty()) newIndex = selector->findData(prev, Qt::UserRole);
    if (newIndex < 0 && selector->count() > 0) newIndex = 0;
    selector->setCurrentIndex(newIndex);

    selector->blockSignals(false);
}

// Create a two-row layout in the group: row 1 = combos (same line), row 2 = Hunk label
static void buildGroupBoxRows(QGroupBox *group,
                              QLabel *classificationLabel,
                              QComboBox *classificationCombo,
                              QLabel *prLabel,
                              QComboBox *prCombo,
                              QLabel **outHunkValueLabel /* may be null */)
{
    QVBoxLayout *vbox = new QVBoxLayout(group);

    // Row 1: combos (same line)
    QHBoxLayout *combosRow = new QHBoxLayout();
    combosRow->addWidget(classificationLabel);
    combosRow->addWidget(classificationCombo);
    combosRow->addSpacing(12);
    combosRow->addWidget(prLabel);
    combosRow->addWidget(prCombo);
    combosRow->addStretch();
    vbox->addLayout(combosRow);

    // Row 2: Hunk label
    QHBoxLayout *hunkRow = new QHBoxLayout();
    QLabel *hunkText = new QLabel("Hunk:", group);
    QLabel *hunkValue = new QLabel("-", group);
    hunkValue->setObjectName("HunkValueLabel");
    hunkRow->addWidget(hunkText);
    hunkRow->addWidget(hunkValue);
    hunkRow->addStretch();
    vbox->addLayout(hunkRow);

    if (outHunkValueLabel) *outHunkValueLabel = hunkValue;

    group->setLayout(vbox);
}

// Default startup highlight specs (defaults REMOVED)
void FileInterface::setDefaultStartupSpecs(QVector<FileInterface::HighlightSpec> &specs)
{
    specs.clear(); // no defaults
}

// ===== JSCPD helpers (no auto) =====
static QString jscpdNormRelNoAuto(const QString &pIn) {
    QString p = pIn;
    p.replace('\\', '/');
    if (p.startsWith("./")) {
        QString tmp = p;
        tmp.remove(0, 2);
        p = tmp;
    }
    return QDir::cleanPath(p);
}

static QColor jscpdColorForIndexNoAuto(int i) {
    int hue = (i * 47) % 360;
    QColor c;
    c.setHsl(hue, 160, 140, 150);
    return c;
}

// =================== FileInterface ===================

FileInterface::FileInterface(QWidget *parent, QString rootParam) : QWidget(parent)
{
    kRootDir = rootParam;
    g_rootDir = kRootDir;

    QVBoxLayout *rootLayout = new QVBoxLayout(this);
    rootLayout->setContentsMargins(6,6,6,6);
    rootLayout->setSpacing(8);

    QMenuBar *menuBarWidget = new QMenuBar(this);
    QMenu *fileMenu = menuBarWidget->addMenu("&File");
    QAction *openLeftAction  = fileMenu->addAction("Open &Left… (manual)");
    QAction *openRightAction = fileMenu->addAction("Open &Right… (manual)");
    fileMenu->addSeparator();
    QAction *quitAction = fileMenu->addAction("&Quit");
    rootLayout->addWidget(menuBarWidget);

    topGroup = new QGroupBox("Context", this);
    classificationLabel = new QLabel("Classification:", topGroup);
    classificationCombo = new QComboBox(topGroup);
    classificationCombo->setMinimumWidth(160);
    prLabel = new QLabel("PR_Number:", topGroup);
    prCombo = new QComboBox(topGroup);
    prCombo->setMinimumWidth(180);

    QLabel *hunkValueLabel = NULL;
    buildGroupBoxRows(topGroup,
                      classificationLabel, classificationCombo,
                      prLabel, prCombo,
                      &hunkValueLabel);
    rootLayout->addWidget(topGroup);

    // --- MAIN SPLITTER WITH TWO PANELS ---
    QSplitter *splitter = new QSplitter(this);
    rootLayout->addWidget(splitter, 1);

    // LEFT PANEL
    leftPanel = new QWidget(splitter);
    {
        QVBoxLayout *leftRoot = new QVBoxLayout(leftPanel);
        leftRoot->setContentsMargins(0,0,0,0);
        leftRoot->setSpacing(6);

        QHBoxLayout *leftFileRow = new QHBoxLayout();
        QLabel *leftLabel = new QLabel("Left (src):", leftPanel);
        leftFileSelector = new QComboBox(leftPanel);
        leftFileSelector->setEditable(false);
        leftFileSelector->setSizeAdjustPolicy(QComboBox::AdjustToContents);
        leftFileRow->addWidget(leftLabel);
        leftFileRow->addWidget(leftFileSelector, 1);
        leftRoot->addLayout(leftFileRow);

        // ✅ use LineNumberViewer instead of QPlainTextEdit
        leftEdit = new LineNumberViewer(leftPanel);
        QFont monospace(QFontDatabase::systemFont(QFontDatabase::FixedFont));
        leftEdit->setFont(monospace);
        leftRoot->addWidget(leftEdit);
    }
    splitter->addWidget(leftPanel);

    // RIGHT PANEL
    rightPanel = new QWidget(splitter);
    {
        QVBoxLayout *rightRoot = new QVBoxLayout(rightPanel);
        rightRoot->setContentsMargins(0,0,0,0);
        rightRoot->setSpacing(6);

        QHBoxLayout *rightFileRow = new QHBoxLayout();
        QLabel *rightLabel = new QLabel("Right (cmp):", rightPanel);
        rightFileSelector = new QComboBox(rightPanel);
        rightFileSelector->setEditable(false);
        rightFileSelector->setSizeAdjustPolicy(QComboBox::AdjustToContents);
        rightFileRow->addWidget(rightLabel);
        rightFileRow->addWidget(rightFileSelector, 1);
        rightRoot->addLayout(rightFileRow);

        // ✅ use LineNumberViewer instead of QPlainTextEdit
        rightEdit = new LineNumberViewer(rightPanel);
        QFont monospace(QFontDatabase::systemFont(QFontDatabase::FixedFont));
        rightEdit->setFont(monospace);
        rightRoot->addWidget(rightEdit);
    }
    splitter->addWidget(rightPanel);

    // View-only already enforced by LineNumberViewer; keep for safety.
    leftEdit->setReadOnly(true);
    rightEdit->setReadOnly(true);

    QObject::connect(openLeftAction,  &QAction::triggered, this, &FileInterface::openLeftFile);
    QObject::connect(openRightAction, &QAction::triggered, this, &FileInterface::openRightFile);
    QObject::connect(quitAction,      &QAction::triggered, this, [this]() {
        if (window()) window()->close();
    });

    QObject::connect(classificationCombo,
                     QOverload<int>::of(&QComboBox::currentIndexChanged),
                     this,
                     &FileInterface::onClassificationChanged);

    QObject::connect(prCombo,
                     QOverload<int>::of(&QComboBox::currentIndexChanged),
                     this,
                     &FileInterface::onPRChanged);

    QObject::connect(leftFileSelector,
                     QOverload<int>::of(&QComboBox::currentIndexChanged),
                     this,
                     &FileInterface::switchLeftFileFromSelector);

    QObject::connect(rightFileSelector,
                     QOverload<int>::of(&QComboBox::currentIndexChanged),
                     this,
                     &FileInterface::switchRightFileFromSelector);

    if (!g_rootDir.isEmpty()) {
        scanRootForPRsAndClasses(g_rootDir);
    }

    classificationCombo->clear();
    QStringList classes = g_class_to_prs.keys();
    classes.sort(Qt::CaseInsensitive);
    classificationCombo->addItems(classes);

    if (classificationCombo->count() > 0) {
        classificationCombo->setCurrentIndex(0);
        onClassificationChanged(0);
    } else {
        prCombo->clear();
        leftFileSelector->clear();
        rightFileSelector->clear();
    }

    setWindowTitle("Two Files Side by Side");
    resize(1200, 750);
    QList<int> sizes;
    sizes << 600 << 600;
    splitter->setSizes(sizes);
}


// --------------------- File menu (manual opens) ---------------------

void FileInterface::openLeftFile()
{
    QString fileName = QFileDialog::getOpenFileName(this, "Open File (manual to Left)");
    if (fileName.isEmpty()) return;

    if (!loadPathInto(fileName, leftEdit)) {
        QMessageBox::warning(this, "Error", "Could not open file.");
        return;
    }

    leftPath = fileName;

    // Clear highlights both panes
    leftSelections.clear();
    rightSelections.clear();
    leftEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
    rightEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());

    setDefaultStartupSpecs(startupSpecs);
    startupHighlightsRan = false;
    runStartupHighlights();

    updateWindowTitle();
}

void FileInterface::openRightFile()
{
    QString fileName = QFileDialog::getOpenFileName(this, "Open File (manual to Right)");
    if (fileName.isEmpty()) return;

    if (!loadPathInto(fileName, rightEdit)) {
        QMessageBox::warning(this, "Error", "Could not open cmp file for right editor.");
        return;
    }

    rightPath = fileName;

    rightSelections.clear();
    rightEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());

    setDefaultStartupSpecs(startupSpecs);
    startupHighlightsRan = false;
    runStartupHighlights();

    updateWindowTitle();
}

// --------------------- Combo handlers ---------------------

void FileInterface::onClassificationChanged(int)
{
    prCombo->blockSignals(true);
    prCombo->clear();

    const QString cls = classificationCombo->currentText();
    const QSet<QString> prsSet = g_class_to_prs.value(cls);
    const QStringList prs = sortedSet(prsSet);
    prCombo->addItems(prs);
    prCombo->blockSignals(false);

    if (prCombo->count() > 0) {
        prCombo->setCurrentIndex(0);
        onPRChanged(0);
    } else {
        leftFileSelector->clear();
        rightFileSelector->clear();
        leftEdit->clear();  leftPath.clear();
        rightEdit->clear(); rightPath.clear();
        QLabel *hunkValue = topGroup->findChild<QLabel*>("HunkValueLabel");
        if (hunkValue) hunkValue->setText("-");
        updateWindowTitle();
    }
}

void FileInterface::onPRChanged(int)
{
    const QString cls = classificationCombo->currentText();
    const QString pr  = prCombo->currentText();

    leftFileSelector->clear();
    leftEdit->clear();  leftPath.clear();
    QLabel *hunkValue = topGroup->findChild<QLabel*>("HunkValueLabel");
    if (hunkValue) hunkValue->setText("-");

    const QStringList cmpFiles = scanAllCmpFilesForPRClass(g_rootDir, pr, cls);
    const QString base = prClassAbsDir(g_rootDir, pr, cls);
    refillSelectorKeepSelection(rightFileSelector, cmpFiles, base);

    if (rightFileSelector->currentIndex() >= 0)
        switchRightFileFromSelector(rightFileSelector->currentIndex());
    else {
        rightEdit->clear(); rightPath.clear();
    }

    updateWindowTitle();
}

// --------------------- File selector switching ---------------------

void FileInterface::switchLeftFileFromSelector(int index)
{
    if (index < 0) return;
    const QString srcPath = leftFileSelector->itemData(index, Qt::UserRole).toString();
    if (srcPath.isEmpty()) return;

    if (!loadPathInto(srcPath, leftEdit)) {
        QMessageBox::warning(this, "Error", "Could not open src file for left editor.");
        return;
    }
    leftPath = srcPath;

    // Clear both panes
    leftSelections.clear();
    rightSelections.clear();
    leftEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
    rightEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());

    setDefaultStartupSpecs(startupSpecs);
    startupHighlightsRan = false;
    runStartupHighlights();

    updateWindowTitle();
}

void FileInterface::switchRightFileFromSelector(int index)
{
    if (index < 0) return;
    const QString cmpPath = rightFileSelector->itemData(index, Qt::UserRole).toString();
    if (cmpPath.isEmpty()) return;

    if (!loadPathInto(cmpPath, rightEdit)) {
        QMessageBox::warning(this, "Error", "Could not open cmp file for right editor.");
        return;
    }
    rightPath = cmpPath;

    QString repoBaseAbs;
    if (repoBaseFromCmpFile(cmpPath, repoBaseAbs)) {
        const QString cls = classificationCombo->currentText();
        const QString pr  = prCombo->currentText();
        const QString prcl = prClassAbsDir(g_rootDir, pr, cls);

        QStringList srcFiles;
        if (isUnder(prcl, repoBaseAbs)) {
            srcFiles = scanSrcFilesUnderRepo(repoBaseAbs);
        }

        refillSelectorKeepSelection(leftFileSelector, srcFiles, prcl);

        if (leftFileSelector->currentIndex() >= 0) {
            const QString srcPath =
                leftFileSelector->itemData(leftFileSelector->currentIndex(), Qt::UserRole).toString();
            if (!srcPath.isEmpty() && loadPathInto(srcPath, leftEdit)) {
                leftPath = srcPath;

                leftSelections.clear();
                rightSelections.clear();
                leftEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
                rightEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
            } else {
                leftEdit->clear(); leftPath.clear();
                leftSelections.clear();
                rightSelections.clear();
                leftEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
                rightEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
            }
        } else {
            leftEdit->clear(); leftPath.clear();
            leftSelections.clear();
            rightSelections.clear();
            leftEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
            rightEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
        }

        QLabel *hunkValue = topGroup->findChild<QLabel*>("HunkValueLabel");
        if (hunkValue) {
            QString tmp = repoBaseAbs;
#ifdef Q_OS_WIN
            tmp.replace('\\','/');
#endif
            const QStringList parts = tmp.split('/', Qt::SkipEmptyParts);
            QString hunk = (parts.size() >= 2) ? parts.at(parts.size()-2) : QString();
            hunkValue->setText(hunk.isEmpty() ? "-" : hunk);
        }
    } else {
        leftFileSelector->clear();
        leftEdit->clear(); leftPath.clear();

        leftSelections.clear();
        rightSelections.clear();
        leftEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());
        rightEdit->setExtraSelections(QList<QTextEdit::ExtraSelection>());

        QLabel *hunkValue = topGroup->findChild<QLabel*>("HunkValueLabel");
        if (hunkValue) hunkValue->setText("-");
    }

    setDefaultStartupSpecs(startupSpecs);
    startupHighlightsRan = false;
    runStartupHighlights();

    updateWindowTitle();
}

// --------------------- highlighting core ---------------------

void FileInterface::updateWindowTitle()
{
    QString leftTitle  = leftPath.isEmpty()  ? "(left: none)"  : leftPath;
    QString rightTitle = rightPath.isEmpty() ? "(right: none)" : rightPath;

    QString windowTitle = QString("Two Files Side by Side  |  %1   ||   %2")
                              .arg(leftTitle, rightTitle);

    setWindowTitle(windowTitle);
}

void FileInterface::jumpToLine(QPlainTextEdit *editor, int lineOneBased)
{
    if (lineOneBased < 1) lineOneBased = 1;

    QTextDocument *document = editor->document();
    QTextBlock block = document->findBlockByNumber(lineOneBased - 1);
    if (!block.isValid()) return;

    QTextCursor cursor(document);
    cursor.setPosition(block.position());
    editor->setTextCursor(cursor);
    editor->centerCursor();
}

int FileInterface::toPos(QPlainTextEdit *editor, int lineOneBased, int colOneBased)
{
    if (lineOneBased < 1) lineOneBased = 1;

    QTextDocument *document = editor->document();
    QTextBlock block = document->findBlockByNumber(lineOneBased - 1);
    if (!block.isValid()) return document->characterCount() - 1;

    int basePosition = block.position();
    int zeroBasedColumn = qMax(0, colOneBased - 1);
    return basePosition + zeroBasedColumn;
}

bool FileInterface::loadPathInto(const QString &path, QPlainTextEdit *targetEditor)
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) return false;
    QTextStream textStream(&file);
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
    textStream.setAutoDetectUnicode(true);
    textStream.setEncoding(QStringConverter::Utf8);
#endif
    targetEditor->setPlainText(textStream.readAll());
    file.close();
    return true;
}

void FileInterface::highlightRange(QPlainTextEdit *editor,
                                   int startLine, int startColumn,
                                   int endLine, int endColumn,
                                   const QColor &color)
{
    QTextDocument *document = editor->document();
    int startPos = toPos(editor, startLine, startColumn);
    int endPos   = toPos(editor, endLine,   endColumn);
    if (endPos < startPos) { int tmp = startPos; startPos = endPos; endPos = tmp; }

    QTextCursor cursor(document);
    cursor.setPosition(startPos);
    cursor.setPosition(endPos, QTextCursor::KeepAnchor);

    QTextEdit::ExtraSelection selection;
    selection.cursor = cursor;
    selection.format.setBackground(QBrush(color));
    selection.format.setForeground(Qt::black);

    if (editor == leftEdit) leftSelections.push_back(selection);
    else                    rightSelections.push_back(selection);
}

void FileInterface::applySelections(QPlainTextEdit *editor)
{
    if (editor == leftEdit) editor->setExtraSelections(leftSelections);
    else                    editor->setExtraSelections(rightSelections);
}

void FileInterface::runStartupHighlights()
{
    bool leftHasText  = leftEdit->document()->characterCount()  > 1;
    bool rightHasText = rightEdit->document()->characterCount() > 1;
    if (!leftHasText && !rightHasText) return;

    // Ensure UI is cleared
    leftSelections.clear();
    rightSelections.clear();
    applySelections(leftEdit);
    applySelections(rightEdit);

    int firstRightDupLine = 0;

    if (!leftPath.isEmpty() && !rightPath.isEmpty()) {
        QString repoBaseAbs;
        if (repoBaseFromCmpFile(rightPath, repoBaseAbs)) {

            const QString cls = classificationCombo->currentText();
            const QString pr  = prCombo->currentText();
            const QString prRootAbs = prClassAbsDir(g_rootDir, pr, cls);

            QString tmp = repoBaseAbs;
#ifdef Q_OS_WIN
            tmp.replace('\\','/');
#endif
            const QStringList parts = tmp.split('/', Qt::SkipEmptyParts);
            QString hunkName = (parts.size() >= 2) ? parts.at(parts.size()-2) : QString();
            QString githubPathName = (parts.size() >= 1) ? parts.at(parts.size()-1) : QString();

            // Prefer repo-level report; if missing, fall back to PR-level
            QString reportPath = QDir(repoBaseAbs).filePath("reports/html/jscpd-report.json");
            QFile rf(reportPath);
            bool usingRepoReport = rf.open(QIODevice::ReadOnly);
            if (!usingRepoReport) {
                reportPath = QDir(prRootAbs).filePath("reports/html/jscpd-report.json");
                rf.setFileName(reportPath);
                usingRepoReport = false;
            }
            if (!rf.isOpen() && !rf.open(QIODevice::ReadOnly)) {
                // No report available
            } else {
                QByteArray bytes = rf.readAll();
                rf.close();

                QJsonParseError perr;
                QJsonDocument doc = QJsonDocument::fromJson(bytes, &perr);
                if (perr.error == QJsonParseError::NoError && doc.isObject()) {
                    QJsonObject root = doc.object();
                    QJsonArray dups  = root.value("duplicates").toArray();

                    // Repo-relative paths
                    QString leftRelRepo  = QDir(repoBaseAbs).relativeFilePath(leftPath);
                    QString rightRelRepo = QDir(repoBaseAbs).relativeFilePath(rightPath);
#ifdef Q_OS_WIN
                    leftRelRepo.replace('\\','/');
                    rightRelRepo.replace('\\','/');
#endif
                    leftRelRepo  = jscpdNormRelNoAuto(leftRelRepo);
                    rightRelRepo = jscpdNormRelNoAuto(rightRelRepo);

                    // PR-relative (with hunk/github)
                    QString leftRelPR  = hunkName + "/" + githubPathName + "/" + leftRelRepo;
                    QString rightRelPR = hunkName + "/" + githubPathName + "/" + rightRelRepo;

                    // Filenames only (super tolerant)
                    QString leftFileName  = QFileInfo(leftPath).fileName();
                    QString rightFileName = QFileInfo(rightPath).fileName();

                    for (int i = 0; i < dups.size(); ++i) {
                        QJsonValue v = dups.at(i);
                        if (!v.isObject()) continue;
                        QJsonObject dup = v.toObject();
                        int linesTotal = dup.value("lines").toInt();

                        QJsonObject firstObj  = dup.value("firstFile").toObject();   // src (left)
                        QJsonObject secondObj = dup.value("secondFile").toObject();  // cmp (right)

                        QString firstName  = jscpdNormRelNoAuto(firstObj.value("name").toString());
                        QString secondName = jscpdNormRelNoAuto(secondObj.value("name").toString());

                        // HUNK filter:
                        if (!usingRepoReport) {
                            bool inHunkFirst  = firstName.contains("/" + hunkName + "/")  || firstName.startsWith(hunkName + "/");
                            bool inHunkSecond = secondName.contains("/" + hunkName + "/") || secondName.startsWith(hunkName + "/");
                            if (!inHunkFirst || !inHunkSecond) continue;
                        }

                        // File pair match — tolerant:
                        bool leftMatch =
                            firstName.endsWith(leftRelRepo)
                            || firstName.endsWith(leftRelPR)
                            || firstName.endsWith("/" + leftFileName)
                            || firstName == leftFileName;

                        bool rightMatch =
                            secondName.endsWith(rightRelRepo)
                            || secondName.endsWith(rightRelPR)
                            || secondName.endsWith("/" + rightFileName)
                            || secondName == rightFileName;

                        if (!leftMatch || !rightMatch) continue;
                        qDebug()<<"Checking: "<< leftFileName <<" and "<<rightFileName;
                        // Coordinates
                        QJsonObject fSL = firstObj.value("startLoc").toObject();
                        QJsonObject fEL = firstObj.value("endLoc").toObject();
                        int fStartLine  = fSL.value("line").toInt(firstObj.value("start").toInt(1));
                        int fStartCol   = fSL.value("column").toInt(1);
                        int fEndLine    = fStartLine + linesTotal - 1;
                        int fEndCol     = fEL.value("column").toInt(fStartCol);
                        qDebug()<<"Highlight Information (src)";
                        qDebug()<<" Start line:"<<fStartLine;
                        qDebug()<<" Start Column:"<<fStartCol;
                        qDebug()<<" End line:"<<fEndLine;
                        qDebug()<<" End Column:"<<fEndCol;

                        QJsonObject sSL = secondObj.value("startLoc").toObject();
                        QJsonObject sEL = secondObj.value("endLoc").toObject();
                        int sStartLine  = sSL.value("line").toInt(secondObj.value("start").toInt(1));
                        int sStartCol   = sSL.value("column").toInt(1);
                        int sEndLine    = sStartLine + linesTotal - 1;
                        int sEndCol     = sEL.value("column").toInt(sStartCol);
                        qDebug()<<"Highlight Information (cmp)";
                        qDebug()<<" Start line:"<<sStartLine;
                        qDebug()<<" Start Column:"<<sStartCol;
                        qDebug()<<" End line:"<<sEndLine;
                        qDebug()<<" End Column:"<<sEndCol;

                        QColor col = jscpdColorForIndexNoAuto(i); // stable color per duplicate index

                        if (leftHasText) {
                            highlightRange(leftEdit, fStartLine, fStartCol, fEndLine, fEndCol, col);
                        }
                        if (rightHasText) {
                            highlightRange(rightEdit, sStartLine, sStartCol, sEndLine, sEndCol, col);
                            if (firstRightDupLine == 0) firstRightDupLine = sStartLine;
                        }
                    }

                    applySelections(leftEdit);
                    applySelections(rightEdit);
                }
            }
        }
    }

    if (firstRightDupLine > 0 && rightEdit != NULL) {
        jumpToLine(rightEdit, firstRightDupLine);
    }

    startupHighlightsRan = true;
}
