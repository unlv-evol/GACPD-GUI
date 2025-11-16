#ifndef FILEINTERFACE_H
#define FILEINTERFACE_H

#include <QWidget>
#include <QVector>
#include <QString>
#include <QTextEdit>
#include <QColor>
#include <QMap>
#include <QStringList>

class QPlainTextEdit;
class QSplitter;
class QWidget;
class QComboBox;
class QGroupBox;
class QLabel;

class FileInterface : public QWidget
{
    Q_OBJECT
public:
    explicit FileInterface(QWidget *parent = nullptr, QString root = "");
    void jumpToLine(QPlainTextEdit *editor, int lineOneBased);

private slots:
    // Menu actions
    void openLeftFile();
    void openRightFile();
    void runStartupHighlights();

    // Global controls (top GroupBox)
    void onClassificationChanged(int index);
    void onPRChanged(int index);

    // File selectors
    void switchLeftFileFromSelector(int index);
    void switchRightFileFromSelector(int index);

private:
    // Loaders / helpers
    void loadInto(QPlainTextEdit *targetEditor);
    bool loadPathInto(const QString &path, QPlainTextEdit *targetEditor);
    void updateWindowTitle();

    // Buckets & selectors
    void addFileToCurrentBucket(const QString &path);
    void refreshSelectorsForCurrentFilters();
    void ensureSelectorSelection(QComboBox *selector, const QString &preferPathIfPresent);

    // Highlighting helpers
    void highlightRange(QPlainTextEdit *editor,
                        int startLine, int startColumn,
                        int endLine,   int endColumn,
                        const QColor &color);
    void applySelections(QPlainTextEdit *editor);
    int toPos(QPlainTextEdit *editor, int lineOneBased, int colOneBased);

    // kept but unused
    bool promptRange(int &startLine, int &startColumn, int &endLine, int &endColumn);

    enum Pane { LeftPane, RightPane };

    struct HighlightSpec {
        Pane pane;
        int startLine;
        int startColumn;
        int endLine;
        int endColumn;
        QColor color;
        HighlightSpec(Pane p, int sl, int sc, int el, int ec, const QColor &c)
            : pane(p), startLine(sl), startColumn(sc), endLine(el), endColumn(ec), color(c) {}
    };

    void setDefaultStartupSpecs(QVector<HighlightSpec> &specs);
    // ---------- UI ----------
    QWidget *root;               // container with VBox (GroupBox on top + splitter below)
    QSplitter *splitter;

    // Top controls (single set)
    QGroupBox *topGroup;
    QLabel *classificationLabel;
    QComboBox *classificationCombo;
    QLabel *prLabel;
    QComboBox *prCombo;

    // LEFT panel (selector + editor)
    QWidget *leftPanel;
    QComboBox *leftFileSelector;
    QPlainTextEdit *leftEdit;

    // RIGHT panel (selector + editor)
    QWidget *rightPanel;
    QComboBox *rightFileSelector;
    QPlainTextEdit *rightEdit;

    // ---------- State ----------
    QString leftPath, rightPath;

    QVector<QTextEdit::ExtraSelection> leftSelections;
    QVector<QTextEdit::ExtraSelection> rightSelections;

    QVector<HighlightSpec> startupSpecs;
    bool startupHighlightsRan = false;

    // Files bucketed by Classification -> PR -> [paths]
    QMap<QString, QMap<QString, QStringList>> fileBuckets;

    // Fixed list of classification options
    QStringList classificationOptions() const { return {"MO", "ED", "NA", "CC", "ERROR"}; }

    // Example PRs for each classification (seeded at startup; you can replace later)
    QMap<QString, QStringList> classificationToDefaultPRs;
};

#endif // FILEINTERFACE_H
