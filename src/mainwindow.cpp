#include "headers/mainwindow.h"
#include "ui_mainwindow.h"

#include <QDateTime>
#include <QMessageBox>
#include <QRegularExpression>
#include <QRegularExpressionValidator>
#include <QPushButton>
#include <QLineEdit>
#include <QPlainTextEdit>
#include <QSettings>
#include <QDebug>
#include <QCloseEvent>
#include <QDir>
#include <QPixmap>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    ui->btnExtra->hide();

    // Optional: placeholder text
    ui->lineText->setPlaceholderText("Enter a Repo Name...");
    ui->lineText_2->setPlaceholderText("Enter a Repo Name...");

    // Date/time control formatting
    ui->dateTimeInput->setDisplayFormat("yyyy-MM-dd HH:mm");
    ui->dateTimeInput->setCalendarPopup(true);   // nice calendar for date picking
    ui->dateTimeInput->setDateTime(QDateTime::currentDateTime());


    // Date/time control formatting
    ui->dateTimeEdit->setDisplayFormat("yyyy-MM-dd HH:mm");
    ui->dateTimeEdit->setCalendarPopup(true);   // nice calendar for date picking
    ui->dateTimeEdit->setDateTime(QDateTime::currentDateTime());

    // Load saved data (tokens etc.)
    loadPersisted();

    // Force the label to have a minimum size and expand
    ui->imageLabel->setMinimumSize(400, 300);
    ui->imageLabel->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    ui->imageLabel->setAlignment(Qt::AlignCenter);

    // Connect button
    connect(ui->btnSubmit, &QPushButton::clicked, this, &MainWindow::onSubmit);
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::onSubmit() {
    const QString origRepo = ui->lineText->text().trimmed();
    const QString divRepo  = ui->lineText_2->text().trimmed();
    const QDateTime from   = ui->dateTimeEdit->dateTime();
    const QString fromIso  = from.toString(Qt::ISODate);
    const QDateTime when   = ui->dateTimeInput->dateTime();
    const QString whenIso  = when.toString(Qt::ISODate);           // 2025-09-16T13:46:00
    const QString tokens   = ui->plainTextEdit->toPlainText();

    // ---- Print to terminal (Qt Creator -> Application Output) ----
    qDebug().noquote() << "Submit clicked:";
    qDebug().noquote() << "  Original Repo:" << origRepo;
    qDebug().noquote() << "  Divergent Repo:" << divRepo;
    qDebug().noquote() << "  Initial DateTime ISO:"<< from;
    qDebug().noquote() << "  DateTime ISO:" << whenIso;
    qDebug().noquote() << "  Tokens (lines):";
    for (const QString &line : tokens.split('\n', Qt::SkipEmptyParts)) {
        qDebug().noquote() << "   - " << line;
    }

    // Save tokens immediately as well (optional, we also save on close)
    savePersisted();

    const QString path = QDir::currentPath() + "/test.png";

    QPixmap pix(path);
    if (pix.isNull()) {
        qWarning() << "Could not load" << path;
        return;
    }
    ui->imageLabel->setPixmap(pix.scaled(ui->imageLabel->size(),
                                         Qt::KeepAspectRatio,
                                         Qt::SmoothTransformation));

    ui->btnExtra->show();
}

void MainWindow::loadPersisted() {
    QSettings s;  // uses org/app from main.cpp

    // Restore token list text (entire plain text)
    const QString tokens = s.value("tokens/plainText", "").toString();
    ui->plainTextEdit->setPlainText(tokens);

    // (Optional) restore window geometry
    restoreGeometry(s.value("ui/geometry").toByteArray());
}

void MainWindow::savePersisted() const {
    QSettings s;

    // Persist token list
    s.setValue("tokens/plainText", ui->plainTextEdit->toPlainText());

    // (Optional) persist geometry
    s.setValue("ui/geometry", saveGeometry());
}

void MainWindow::closeEvent(QCloseEvent *event) {
    savePersisted();
    QMainWindow::closeEvent(event);
}
