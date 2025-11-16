#ifndef CODEEDITOR_H
#define CODEEDITOR_H

#include <QPlainTextEdit>
#include <QWidget>
#include <QPaintEvent>
#include <QResizeEvent>
#include <QTextBlock>

class LNAGutter;

class LineNumberViewer : public QPlainTextEdit {
    Q_OBJECT
public:
    explicit LineNumberViewer(QWidget *parent = nullptr);

    // Convenient loaders
    void setContent(const QString &text);
    bool loadFile(const QString &filePath, const QByteArray &codec = QByteArray("UTF-8"));

    int gutterWidth() const;
    void paintGutter(QPaintEvent *event);

protected:
    void resizeEvent(QResizeEvent *event) override;

private slots:
    void onBlockCountChanged(int);
    void onUpdateRequest(const QRect &rect, int dy);

private:
    QWidget *m_gutter;
};

class LNAGutter : public QWidget {
public:
    explicit LNAGutter(LineNumberViewer *v) : QWidget(v), viewer(v) {}
    QSize sizeHint() const override { return { viewer->gutterWidth(), 0 }; }
protected:
    void paintEvent(QPaintEvent *e) override { viewer->paintGutter(e); }
private:
    LineNumberViewer *viewer;
};


#endif // CODEEDITOR_H
