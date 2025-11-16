#include "headers/CodeEditor.h"
#include <QPainter>
#include <QTextBlock>
#include <QPainter>
#include <QFile>
#include <QTextStream>

LineNumberViewer::LineNumberViewer(QWidget *parent)
    : QPlainTextEdit(parent),
    m_gutter(new LNAGutter(this))
{
    // --- Viewer-only: absolutely no editing/selection/caret ---
    setReadOnly(true);
    setTextInteractionFlags(Qt::NoTextInteraction);
    setUndoRedoEnabled(false);
    setCursorWidth(0);
    viewport()->setCursor(Qt::ArrowCursor);
    setContextMenuPolicy(Qt::NoContextMenu);

    // --- Nice defaults for code/text viewing ---
    QFont f = font();
#if defined(Q_OS_WIN)
    f.setFamily(QStringLiteral("Consolas"));
#else
    f.setFamily(QStringLiteral("Monospace"));
#endif
    f.setStyleHint(QFont::Monospace);
    setFont(f);
    setWordWrapMode(QTextOption::NoWrap);
    setTabStopDistance(fontMetrics().horizontalAdvance(QLatin1Char(' ')) * 4);

    // Wire scrolling/invalidations to gutter
    connect(this, &QPlainTextEdit::blockCountChanged, this, &LineNumberViewer::onBlockCountChanged);
    connect(this, &QPlainTextEdit::updateRequest,     this, &LineNumberViewer::onUpdateRequest);

    onBlockCountChanged(0);
}

void LineNumberViewer::setContent(const QString &text) {
    // Avoid flashing by blocking signals while replacing text
    const bool wasBlocked = blockSignals(true);
    setPlainText(text);
    blockSignals(wasBlocked);
    // Ensure gutter width adapts to new line count
    onBlockCountChanged(0);
}

bool LineNumberViewer::loadFile(const QString &filePath, const QByteArray &codec) {
    QFile f(filePath);
    if (!f.open(QIODevice::ReadOnly)) return false;
    QTextStream ts(&f);
    setContent(ts.readAll());
    return true;
}

int LineNumberViewer::gutterWidth() const {
    int digits = 1;
    int max = qMax(1, blockCount());
    while (max >= 10) { max /= 10; ++digits; }
    const int pad = 6; // left-right padding total
    return pad + fontMetrics().horizontalAdvance(QLatin1Char('9')) * digits + 6; // + separator inset
}

void LineNumberViewer::onBlockCountChanged(int) {
    setViewportMargins(gutterWidth(), 0, 0, 0);
}

void LineNumberViewer::onUpdateRequest(const QRect &rect, int dy) {
    if (dy) m_gutter->scroll(0, dy);
    else    m_gutter->update(0, rect.y(), m_gutter->width(), rect.height());

    if (rect.contains(viewport()->rect()))
        onBlockCountChanged(0);
}

void LineNumberViewer::resizeEvent(QResizeEvent *e) {
    QPlainTextEdit::resizeEvent(e);
    const QRect cr = contentsRect();
    m_gutter->setGeometry(QRect(cr.left(), cr.top(), gutterWidth(), cr.height()));
}

void LineNumberViewer::paintGutter(QPaintEvent *event) {
    QPainter p(m_gutter);

    // Background gutter (neutral, no highlight)
    p.fillRect(event->rect(), QColor(36, 36, 36));     // dark matte
    // Separator line between gutter and text
    p.setPen(QColor(64, 64, 64));
    p.drawLine(m_gutter->width()-1, event->rect().top(), m_gutter->width()-1, event->rect().bottom());

    // Use the editor's palette for text for consistency with dark/light themes
    const QColor numColor = palette().color(QPalette::Disabled, QPalette::Text).isValid()
                                ? palette().color(QPalette::Disabled, QPalette::Text)
                                : QColor(170, 170, 170);

    QTextBlock block = firstVisibleBlock();
    int blockNumber  = block.blockNumber();
    int top    = (int)blockBoundingGeometry(block).translated(contentOffset()).top();
    int bottom = top + (int)blockBoundingRect(block).height();

    while (block.isValid() && top <= event->rect().bottom()) {
        if (block.isVisible() && bottom >= event->rect().top()) {
            const QString number = QString::number(blockNumber + 1);
            p.setPen(numColor);
            p.drawText(0, top, m_gutter->width()-6, fontMetrics().height(),
                       Qt::AlignRight | Qt::AlignVCenter, number);
        }
        block = block.next();
        top = bottom;
        bottom = top + (int)blockBoundingRect(block).height();
        ++blockNumber;
    }
}
