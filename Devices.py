from subprocess import call
import sqlite3
import sys
import os.path
import shutil
import subprocess


class Device:
    def __init__(self):
        self.family = ""
        self.device = ""
        self.description = ""


    def __init__(self, family, device, desc=""):
        self.family = family
        self.device = device
        self.description = desc

    __str__ = lambda self: "Housecode:{} Devicecode:{} Description:{}".format(
        self.family, self.device, self.description)

    __repr__ = __str__

    def __eq__(self, other):
        return (self.device == other.device) and (self.family == other.family)

    def enable(self):
        return subprocess.check_output(["sudo", "./send", self.family, self.device, "1"])


    def disable(self):
        return subprocess.check_output(["sudo", "./send", self.family, self.device, "0"])


class DeviceManager:
    def __init__(self):
        if os.path.isfile("devices.sqlite"):
            shutil.copyfileobj("devices.sqlite", "backup_devices.sqlite")

        self.connection = sqlite3.connect("devices.sqlite")
        c = self.connection.cursor()
        c.execute(
            'CREATE TABLE "device" ("housecode" VARCHAR NOT NULL , "devicecode" VARCHAR NOT NULL , "description" TEXT, PRIMARY KEY ("housecode", "devicecode"))')
        c.execute(
            'CREATE TABLE "devicelog" ("logID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , "housecode" VARCHAR NOT NULL , "devicecode" VARCHAR NOT NULL , "switch" VARCHAR NOT NULL , "logtime" DATETIME NOT NULL  DEFAULT CURRENT_TIMESTAMP)')
        c.execute(
            'CREATE TABLE "devicestatus" ("housecode" VARCHAR NOT NULL , "devicecode" VARCHAR NOT NULL , "status" BOOL NOT NULL , "updatetime" DATETIME NOT NULL  DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY ("housecode", "devicecode"))')
        self.connection.commit()


    def __init__(self, sqlitefile):
        self.connection = sqlite3.connect(sqlitefile)
        self.devices = []
        tmpd = self.statusDevices()
        for row in tmpd:
            d = Device(row[0], row[1], row[2])
            self.devices.append(d)


    def addDevice(self, family, device, description, currentStatus):
        d = Device(family, device, description)
        c = self.connection.cursor()
        v = (family, device, description,)
        c.execute('INSERT INTO device(housecode, devicecode, description) VALUES(?,?,?);', v)
        v = (family, device, currentStatus,)
        c.execute('INSERT INTO devicestatus(housecode, devicecode, status) VALUES(?,?,?);', v)

        self.connection.commit()
        # push to sqlite
        self.devices.append(d)
        return "OK"

    def statusDevices(self):
        c = self.connection.cursor()
        c.execute('SELECT device.*, devicestatus.status, devicestatus.updatetime FROM device ' +
                  'LEFT OUTER JOIN devicestatus  ON (device.housecode = devicestatus.housecode) ' +
                  'AND (device.devicecode = devicestatus.devicecode)')
        # get all devies
        return c.fetchall()

    def switchDeviceStatus(self, housecode, devicecode, newStatus):
        d = Device(housecode, devicecode)
        try:
            index = self.devices.index(d)
        except ValueError:
            return "Device is not in list"
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise

        if newStatus:
            self.devices[index].enable()
        else:
            self.devices[index].disable()

        c = self.connection.cursor()
        v = (housecode, devicecode,)
        c.execute("SELECT status FROM devicestatus WHERE housecode=? AND devicecode=?;", v)
        o = c.fetchall()
        oldStatus = "?"
        if (len(o) == 0):
            print("No device status found. Corrupt database?")
        elif (len(o) == 1):
            oldStatus = o[0][0]
        else:
            print("More than one status found. Corrupt database?")

        # save the new status
        v = (housecode, devicecode, newStatus,)
        c.execute("INSERT OR REPLACE INTO devicestatus(housecode, devicecode, status) VALUES(?,?,?);", v)

        statusString = "1" if newStatus else "0"
        v = (housecode, devicecode, str(oldStatus) + "->" + statusString)
        c.execute("INSERT INTO devicelog(housecode, devicecode, switch) VALUES(?,?,?);", v)
        self.connection.commit()
        return "OK"

    def close(self):
        self.connection.close()


if __name__ == '__main__':
    dm = DeviceManager("devices.sqlite")
    print(dm.statusDevices())
    dm.switchDeviceStatus("1111", "111", True)
    print(dm.devices)
    dm.close()