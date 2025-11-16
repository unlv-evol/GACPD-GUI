#include "headers/mainwindow.h"
#include "headers/FileInterface.h"
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
#include <QFileInfo>
#include <QOperatingSystemVersion>
#include <QProcess>
#include <QStandardPaths>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    ui->btnExtra->hide();

    // Optional: placeholder text
    ui->lineText->setPlaceholderText("Enter a Repo Name...");
    ui->lineText_2->setPlaceholderText("Enter a Repo Name...");
    ui->lineText_3->setPlaceholderText("Enter a Project Name...");

    ui->lineText->setText("apache/kafka");
    ui->lineText_2->setText("linkedin/kafka");

    // Date/time control formatting
    ui->dateInput->setDisplayFormat("yyyy-MM-dd");
    ui->dateInput->setCalendarPopup(true);   // nice calendar for date picking
    ui->dateInput->setDateTime(QDateTime::currentDateTime());


    // Date/time control formatting
    ui->dateEdit->setDisplayFormat("yyyy-MM-dd");
    ui->dateEdit->setCalendarPopup(true);   // nice calendar for date picking
    ui->dateEdit->setDateTime(QDateTime::currentDateTime());

    ui->dateInput->setDate(QDate(2022, 06, 22));
    ui->dateEdit->setDate(QDate(2022, 06, 8));

    // Load saved data (tokens etc.)
    loadPersisted();

    // Force the label to have a minimum size and expand
    ui->imageLabel->setMinimumSize(400, 300);
    ui->imageLabel->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
    ui->imageLabel->setAlignment(Qt::AlignCenter);

    // Connect button
    connect(ui->btnSubmit, &QPushButton::clicked, this, &MainWindow::onSubmit);

    // Connect button
    connect(ui->btnExtra, &QPushButton::clicked, this, &MainWindow::onAdvanced);
}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::showMessage(const QString &message, unsigned int id) {
    static QMessageBox* msgBox = nullptr;

    if (!msgBox) {
        msgBox = new QMessageBox;
        msgBox->setWindowTitle("Current Run Information");
        msgBox->setAttribute(Qt::WA_DeleteOnClose, false); // Do not delete when closed
    }

    msgBox->setText(message);

    // Set buttons based on id
    if (id == 151) {
        msgBox->setStandardButtons(QMessageBox::Ok);
    } else {
        msgBox->setStandardButtons(QMessageBox::NoButton); // No buttons
    }

    // Bring to front
    msgBox->raise();
    msgBox->activateWindow();
    QApplication::beep();

    if (!msgBox->isVisible()) {
        msgBox->show(); // Non-blocking
    }

    msgBox->update();
    QApplication::processEvents();
}

void MainWindow::onAdvanced() {
    const QString origRepo = ui->lineText->text().trimmed();
    const QString divRepo  = ui->lineText_2->text().trimmed();
    const QDateTime from   = ui->dateEdit->dateTime();
    const QString fromIso  = from.toString(Qt::ISODate);
    const QDateTime when   = ui->dateInput->dateTime();
    const QString whenIso  = when.toString(Qt::ISODate);           // 2025-09-16T13:46:00
    const QString tokens   = ui->plainTextEdit->toPlainText();
    const QString projName = ui->lineText_3->text().trimmed();

    QString  results =  QDir::currentPath() + "/Results/Repos_results/"+projName;
    qDebug()<<results;
    FileInterface *f = new FileInterface(nullptr, results);
    f->setAttribute(Qt::WA_DeleteOnClose); // cleans up when user closes
    f->setWindowFlag(Qt::Window, true);    // ensures it's a top-level window
    f->show();
    f->raise();
    f->activateWindow();

}

static QString detectPython(const QString &venvDir = QString()) {
#ifdef Q_OS_WIN
    if (!venvDir.isEmpty()) {
        QString cand = venvDir + "/Scripts/python.exe";
        if (QFileInfo::exists(cand)) return cand;
    }
    // Works if the Python Launcher is installed
    if (QStandardPaths::findExecutable("py").size()) return "py";
    return "python"; // fallback (PATH)
#else
    if (!venvDir.isEmpty()) {
        QString cand = venvDir + "/bin/python3";
        if (QFileInfo::exists(cand)) return cand;
    }
    if (QStandardPaths::findExecutable("python3").size()) return "python3";
    return "python";
#endif
}

bool runPythonOnce(const QString &script, const QStringList &args) {
    QProcess p;
    p.start(detectPython(), QStringList() << script << args);
    if (!p.waitForStarted(5000)) return false;
    p.waitForFinished(-1);

    QString output = p.readAllStandardOutput();
    QString errorOutput = p.readAllStandardError();

    // Pretty printing function
    auto printSection = [](const QString &title, const QString &content, const QString &colorCode) {
        if (!content.trimmed().isEmpty()) {
            // Use ANSI colors if terminal supports them
            QString header = QString("\033[1m%1\033[0m").arg(title); // bold title
            QString colored = QString("%1%2\033[0m").arg(colorCode, content.trimmed());
            qDebug().noquote() << header << "\n" << colored << "\n";
        }
    };

    // Print errors in red, normal output in green
    printSection("⚠ Python stderr:", errorOutput, "\033[31m"); // red
    printSection("📜 Python stdout:", output, "\033[32m");     // green


    return true;
}

void MainWindow::onSubmit() {
    const QString origRepo = ui->lineText->text().trimmed();
    const QString divRepo  = ui->lineText_2->text().trimmed();
    const QDateTime from   = ui->dateEdit->dateTime();
    const QString fromIso  = from.toString(Qt::ISODate);
    const QDateTime when   = ui->dateInput->dateTime();
    const QString whenIso  = when.toString(Qt::ISODate);           // 2025-09-16T13:46:00
    const QString tokens   = ui->plainTextEdit->toPlainText();
    const QString projName = ui->lineText_3->text().trimmed();

    // ---- Print to terminal (Qt Creator -> Application Output) ----
    qDebug().noquote() << "Submit clicked:";
    qDebug().noquote() << "  Original Repo:" << origRepo;
    qDebug().noquote() << "  Divergent Repo:" << divRepo;
    qDebug().noquote() << "  Initial DateTime ISO:"<< fromIso;
    qDebug().noquote() << "  DateTime ISO:" << whenIso;
    qDebug().noquote() << "  Project Name:" << projName;
    qDebug().noquote() << "  Tokens (lines):";
    for (const QString &line : tokens.split('\n', Qt::SkipEmptyParts)) {
        qDebug().noquote() << "   - " << line;
    }

    // Save tokens immediately as well (optional, we also save on close)
    savePersisted();
    showMessage("Currently Running GACPD - Please Wait a few minutes.", 0);
    QString script = QDir::currentPath()+"/GACPD/gacpd.py";
    QStringList args = {
        "-p", origRepo,
        "-d", divRepo,
        "-sd", fromIso.split("T")[0]+"T00:00:00Z",
        "-ed", whenIso.split("T")[0]+"T23:59:59Z",
        "-n", projName
    };

    QString newOrigRepo = origRepo.split("/").join("_");
    QString newDivRepo = divRepo.split("/").join("_");

    if(runPythonOnce(script, args)){
        const QString path = QDir::currentPath() + "/"+projName+"-"+newOrigRepo+"-"+newDivRepo;

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
    showMessage("GACPD has finished running - Click \"Advanced Resutls\" for more information.", 151);
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

    // Also persist to file: GACPD/tokens.txt
    QString baseDir = QDir::currentPath();
    QString filePath = baseDir + "/tokens.txt";

    QFile file(filePath);
    if (file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&file);
        out << ui->plainTextEdit->toPlainText();
        file.close();
    } else {
        QMessageBox::warning(nullptr, "Save Error",
                             "Could not save tokens to:\n" + filePath);
    }
}

void MainWindow::closeEvent(QCloseEvent *event) {
    savePersisted();
    QMainWindow::closeEvent(event);
}
