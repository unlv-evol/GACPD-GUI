#include "headers/mainwindow.h"

#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    // These two lines define where QSettings will persist your data
    QCoreApplication::setOrganizationName("Evol");          // pick anything
    QCoreApplication::setApplicationName("GACPD-GUI");      // your app name

    MainWindow w;
    w.show();
    return a.exec();
}
