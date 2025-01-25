import sys
import math
import argparse
import asyncio
from struct import pack, unpack_from
from enum import Enum
import io
import os
from PIL import Image
from bleak import BleakScanner, BleakClient

# Enumerations

class SID(Enum):
    UNKNOWN = -1, -1
    SUPPORT_FUNCTION_AND_VERSION_INFO = 0, 0
    DEVICE_INFO_SERVICE = 0, 1
    SUPPORT_FUNCTION_INFO = 0, 2
    SHUT_DOWN = 1, 0
    RESET = 1, 1
    AUTO_SLEEP_SETTINGS = 1, 2
    BLE_CONNECT = 1, 3
    PRINT_IMAGE_DOWNLOAD_START = 16, 0
    PRINT_IMAGE_DOWNLOAD_DATA = 16, 1
    PRINT_IMAGE_DOWNLOAD_END = 16, 2
    PRINT_IMAGE_DOWNLOAD_CANCEL = 16, 3
    PRINT_IMAGE = 16, 128
    REJECT_FILM_COVER = 16, 129
    FW_DOWNLOAD_START = 32, 0
    FW_DOWNLOAD_DATA = 32, 1
    FW_DOWNLOAD_END = 32, 2
    FW_UPGRADE_EXIT = 32, 3
    FW_PROGRAM_INFO = 32, 16
    FW_DATA_BACKUP = 32, 128
    FW_UPDATE_REQUEST = 32, 129
    XYZ_AXIS_INFO = 48, 0
    LED_PATTERN_SETTINGS = 48, 1
    AXIS_ACTION_SETTINGS = 48, 2
    LED_PATTERN_SETTINGS_DOUBLE = 48, 3
    POWER_ONOFF_LED_SETTING = 48, 4
    ADDITIONAL_PRINTER_INFO = 48, 16
    PRINTER_HEAD_LIGHT_CORRECT_INFO = 48, 128
    PRINTER_HEAD_LIGHT_CORRECT_SETTINGS = 48, 129
    CAMERA_SETTINGS = 128, 0
    CAMERA_SETTINGS_GET = 128, 1
    URL_UPLOAD_INFO = 129, 0
    URL_PICTURE_UPLOAD_START = 129, 1
    URL_PICTURE_UPLOAD = 129, 2
    URL_PICTURE_UPLOAD_END = 129, 3
    URL_AUDIO_UPLOAD_START = 129, 4
    URL_AUDIO_UPLOAD = 129, 5
    URL_AUDIO_UPLOAD_END = 129, 6
    URL_UPLOAD_ADDRESS = 129, 7
    URL_UPLOAD_DATA_COMPLETE = 129, 8
    LIVE_VIEW_START = 138, 0
    LIVE_VIEW_RECEIVE = 138, 1
    LIVE_VIEW_STOP = 138, 2
    LIVE_VIEW_TAKE_PICTURE = 138, 16
    POST_VIEW_UPLOAD_START = 138, 32
    POST_VIEW_UPLOAD = 138, 33
    POST_VIEW_UPLOAD_END = 138, 34
    POST_VIEW_PRINT = 138, 48
    FRAME_PICTURE_DOWNLOAD_START = 131, 0
    FRAME_PICTURE_DOWNLOAD = 131, 1
    FRAME_PICTURE_DOWNLOAD_END = 131, 2
    FRAME_PICTURE_NAME_SETTING = 131, 3
    FRAME_PICTURE_NAME_GET = 131, 4
    CAMERA_LOG_SUBTOTAL_START = 132, 0
    CAMERA_LOG_SUBTOTAL_DATA = 132, 1
    CAMERA_LOG_SUBTOTAL_CLEAR = 132, 2
    CAMERA_LOG_DATE_START = 132, 3
    CAMERA_LOG_DATE_DATA = 132, 4
    CAMERA_LOG_DATE_CLEAR = 132, 5
    CAMERA_LOG_FILTER_START = 132, 6
    CAMERA_LOG_FILTER_DATA = 132, 7
    CAMERA_LOG_FILTER_CLEAR = 132, 8

class ResultCode(Enum):
    OK = 0
    PRINTER_BUSY = 1
    CAMERA_BUSY = 2
    PENDING_RESPONSE = 127
    SID_NOT_SUPPORTED = 128
    PARAMETER_ERROR = 129
    SEQUENCE_ERROR = 130
    OTHER_USED_ERROR = 131
    SECURITY_CODE_ERROR = 132
    TIME_OUT_ERROR = 133
    LOW_POWER_ERROR = 144
    BATTERY_NO_MOUNT_ERROR = 145
    BATTERY_OVERHEAT_ERROR = 146
    BATTERY_CHARGE_FAULT_ERROR = 147
    FIRMWARE_NO_UPDATE_DATA_ERROR = 160
    FIRMWARE_UPDATE_DATA_ERROR = 161
    FIRMWARE_UPDATE_DATA_FAILURE_ERROR = 162
    FIRMWARE_UPDATE_SDCARD_ERROR = 163
    CAMERA_COVER_OPEN_ERROR = 176
    CAMERA_NO_FILM_ERROR = 177
    CAMERA_NO_PAPER_ERROR = 178
    CAMERA_IMAGE_ERROR = 179
    CAMERA_JAMMED_ERROR = 180
    CAMERA_PRINT_FAULT_ERROR = 181
    MEMORY_FULL_ERROR = 192
    POST_VIEW_PRINT_ERROR = 193
    NOW_PRINTING_ERROR = 194
    SW_ABNORMALITY_ERROR = 240
    HW_ABNORMALITY_ERROR = 241
    MECHA_ABNORMALITY_ERROR = 242
    UNKNOWN = -1

class DeviceInfoType(Enum):
    MANUFACTURER_NAME = 0
    MODEL_NUMBER = 1
    SERIAL_NUMBER = 2
    HW_REVISION = 3
    FW_REVISION = 4
    SW_REVISION = 5
    SYSTEM_ID = 6
    REGULATORY_DATA = 7
    PNP_ID = 8

class SupportFunctionInfoType(Enum):
    IMAGE_SUPPORT_INFO = 0
    BATTERY_INFO = 1
    PRINTER_FUNCTION_INFO = 2
    PRINT_HISTORY_INFO = 3
    CAMERA_FUNCTION_INFO = 4
    CAMERA_HISTORY_INFO = 5

class PictureType(Enum):
    PICINF_PICTYPE_NONE = 0, ".none"
    PICINF_PICTYPE_BMP = 1, ".bmp"
    PICINF_PICTYPE_JPEG = 2, ".jpg"
    PICINF_PICTYPE_PNG = 4, ".png"
    PICINF_PICTYPE_LINEORDER = 16, ".unknown"

class PicturePrintOption(Enum):
    PICINF_PICOP_NONE = 0
    PICINF_PICOP_1_STPRT = 16
    PICINF_PICOP_FORCED_PRT = 32
    PICINF_PICOP_ONLY_ONE = 64
    PICINF_PICOP_NOSAVE = 128
    PICINF_PICOP_3DLUT = 8

class PrinterResults(Enum):
    NORMAL_TERMINATION = 0
    CAMERA_BACK_DOOR_OPEN = 1
    NO_FILM_ERROR = 2
    PRINTER_PROCESSING = 127
    ERROR_FLAG = 240
    OTHER_PRILIMINARY = -1

class AdditionalPrinterInfoType(Enum):
    VOLTAGE_INFO = 0
    COLOR_INFO = 1

class CameraColor(Enum):
    WHITE = 0
    BROWN = 1
    UNKNOWN = -1

class AutoSleepSettingsMode(Enum):
    GET_CURRENT_SLEEP_SETTING = 0
    GET_PROVITIONAL_SLEEP_SETTING = 1
    GET_DEFAULT_SLEEP_SETTING = 2
    EXTEND_CURRENT_SLEEP_SETTING = 3
    SET_PROVITIONAL_SLEEP_SETTING = 4
    SET_DEFAULT_SLEEP_SETTING = 5

class PrinterMountedHeadType(Enum):
    FUTABA = 0
    TOHOKU = 1
    UNKNOWN = -1

# Utilities

def isKthBitSet(byte, pos):
    return ((1 << pos) & byte) >= 1

def slice_image(imageByteArray, frameSize):
    frames = list()
    frame = b''
    for i in range(len(imageByteArray)):
        frame += pack('>B', imageByteArray[i])
        if (i + 1) % frameSize == 0:
            frames.append(frame)
            frame = b''
        elif i == len(imageByteArray) - 1:
            # pad the last slice with x00
            for j in range(frameSize - len(frame)):
                frame += b'\x00'
            frames.append(frame)
    return frames

# Messages

class Message:
    def __init__(self, signature, sid, data, resultCode = ResultCode.UNKNOWN, size = 0, checksum = 0):
        self.signature = signature # 2 chars
        self.size = size # unsigned short
        self.sid = sid # (unsigned char, unsigned char)
        self.resultCode = resultCode # unsigned char, only InboundMessage
        self.data = data # bytearray
        self.checksum = checksum # unsigned char

    def __str__(self):
        return f'Signature: {self.signature.decode()}, size: {self.size}, SID: {self.sid.name}, result code: {self.resultCode.name}, data: {self.data.hex(" ", 1)}, checksum: {self.checksum}'

    def get_content(self):
        return self.signature + pack('>H', self.size) + pack('>B', self.sid.value[0]) + pack('>B', self.sid.value[1]) + (pack('>B', self.resultCode.value) if self.resultCode != ResultCode.UNKNOWN else b'') + self.data
    
    def calculate_checksum(self):
        return (255 - (sum(self.get_content()) & 255)) & 255

class OutboundMessage(Message):
    def __init__(self, sid, data):
        super().__init__(b'\x41\x62', sid, data)
        self.size = self.calculate_size(data)
        self.checksum = self.calculate_checksum()
    
    def calculate_size(self, bytearray):
        return 7 + len(bytearray)
    
    def get_payload(self):
        return self.get_content() + pack('>B', self.checksum)

class InboundMessage(Message):
    def __init__(self, signature, size, sid, resultCode, data, checksum):
        super().__init__(signature, sid, data, resultCode, size, checksum)
    
    def validate_signature(self):
        return self.signature == b'\x61\x42'
    
    def validate_checksum(self):
        return self.calculate_checksum() == self.checksum

# Requests

class Request:
    def __init__(self, sid, data = b''):
        self.message = OutboundMessage(sid, data)
    
    def __str__(self):
        return f'SID: {self.message.sid.name}, data: {self.message.data.hex(" ", 1)}'

class SupportFunctionaAndVersionInfoRequest(Request):
    def __init__(self):
        super().__init__(SID.SUPPORT_FUNCTION_AND_VERSION_INFO)

class DeviceInfoRequest(Request):
    def __init__(self, type): # DeviceInfoType
        data = pack('>B', type.value)
        super().__init__(SID.DEVICE_INFO_SERVICE, data)

class SupportFunctionInfoRequest(Request):
    def __init__(self, type): # FunctionInfoType
        data = pack('>B', type.value)
        super().__init__(SID.SUPPORT_FUNCTION_INFO, data)

class AdditionalPrinterInfoRequest(Request):
    def __init__(self, type): # AdditionalPrinterInfoType
        data = pack('>B', type.value)
        super().__init__(SID.ADDITIONAL_PRINTER_INFO, data)

class AutoSleepSettingsRequest(Request):
    def __init__(self, mode, time1, time2, time3, time4): # AutoSleepSettingsMode, unsigned short, unsigned short, unsigned short, unsigned short
        data = pack('>BBBBHHHH', mode.value, 0, 0, 0, time1, time2, time3, time4)
        super().__init__(SID.AUTO_SLEEP_SETTINGS, data)

class ImageTransferStartRequest(Request):
    def __init__(self, pictureType, picturePrintOption, imageSize): # PictureType, PicturePrintOption, unsigned int
        data = pack('>BBBBI', pictureType.value[0], picturePrintOption.value, 0, 0, imageSize)
        super().__init__(SID.PRINT_IMAGE_DOWNLOAD_START, data)

class ImageFrameTransferRequest(Request):
    def __init__(self, frameNumber, imageFrameData): # unsigned int, bytearray
        data = pack('>I', frameNumber) + imageFrameData
        super().__init__(SID.PRINT_IMAGE_DOWNLOAD_DATA, data)

class ImageTransferEndRequest(Request):
    def __init__(self):
        super().__init__(SID.PRINT_IMAGE_DOWNLOAD_END)

class ImagePrintRequest(Request):
    def __init__(self):
        super().__init__(SID.PRINT_IMAGE)

class LightCorrectInfoRequest(Request):
    def __init__(self):
        super().__init__(SID.PRINTER_HEAD_LIGHT_CORRECT_INFO)

# Responses

class Response:
    def __init__(self, payload):
        self.message = self.parse(payload) # bytearray -> InboundMessage
        self.valid = self.validate()

    def __str__(self):
        return f'SID: {self.message.sid.name}, result code: {self.message.resultCode.name}, data: {self.message.data.hex(" ", 1)}'
    
    def parse(self, payload):
        signature, size, modeCode, typeCode, resultCode = unpack_from('>2sHBBB', payload)
        data = payload[7:-1]
        checksum, = unpack_from('>B', payload, size-1)
        return InboundMessage(signature, size, SID((modeCode, typeCode)), ResultCode(resultCode), data, checksum)
    
    def validate(self):
        if self.message.validate_signature():
            if self.message.validate_checksum():
                if self.message.resultCode == ResultCode.OK:
                    return True
                else:
                    print('Error code %s' % self.message.resultCode.name)
            else:
                print('Invalid checksum!')
        else:
            print('Invalid signature!')
        return False

class SupportFunctionaAndVersionInfoResponse():
    def __init__(self, data):
        self.supportFunctionInfo, self.deviceInfoVersion, self.supportImgInfoVersion, self.batteryInfoVersion, self.printerFuncInfoVersion, self.printerHistoryInfoVersion, self.cameraFuncInfoVersion, self.cameraHistoryInfoVersion = unpack_from('>BBBBBBBB', data)
    
    def __str__(self):
        return f'Support function info: {self.supportFunctionInfo}, device info version: {self.deviceInfoVersion}, support img info version: {self.supportImgInfoVersion}, battery info version: {self.batteryInfoVersion}, printer func info version: {self.printerFuncInfoVersion}, printer history info version: {self.printerHistoryInfoVersion}, camera func info version: {self.cameraFuncInfoVersion}, camera history info version: {self.cameraHistoryInfoVersion}'
    
    def isCameraLogAvailable(self):
        return isKthBitSet(self.supportFunctionInfo, 4)

    def isFrameSetAvailable(self):
        return isKthBitSet(self.supportFunctionInfo, 3)
    
    def isUrlUploadAvailable(self):
        return isKthBitSet(self.supportFunctionInfo, 2)

    def isLiveViewAvailable(self):
        return isKthBitSet(self.supportFunctionInfo, 1)

    def isPrintFunctionAvailable(self):
        return isKthBitSet(self.supportFunctionInfo, 0)

class DeviceInfoResponse():
    def __init__(self, data):
        type, = unpack_from('>B', data)
        self.type = DeviceInfoType(type)
        valueSize, = unpack_from('>B', data, 1)
        value, = unpack_from('>%is' % valueSize, data, 2)
        self.value = value.decode()

    def __str__(self):
        return f'Device info type: {self.type.name}, value: {self.value}'

class ImageSupportInfo():
    def __init__(self, width, height, picType, picOption, size):
        self.width = width # unsigned short
        self.height = height # unsigned short
        self.picType = picType # unsigned char
        self.picOption = picOption # unsigned char
        self.size = size # unsigned int
    
    def __str__(self):
        return f'Width: {self.width}, height: {self.height}, size: {self.size}, picture type: {self.picType}, picture option: {self.picOption}'
    
    def is3DLutAvailable(self):
        return isKthBitSet(self.picOption, 3)

class BatteryInfo():
    def __init__(self, batteryLevel, batteryCapacity, chargerType, chargerState):
        self.batteryCapacity = batteryCapacity # unsigned char
        self.batteryLevel = batteryLevel # unsigned char
        self.chargerState = chargerState # unsigned char
        self.chargerType = chargerType # unsigned char
    
    def __str__(self):
        return f'Battery capacity: {self.batteryCapacity}, battery level: {self.batteryLevel}, charger state: {self.chargerState}, charger type: {self.chargerType}'
    
    def is_good(self):
        i2 = self.batteryLevel & 7
        if i2 != 0:
            return i2 == 1 or i2 == 2 or i2 == 3
        else:
            return False

class PrinterFunctionInfo():
    def __init__(self, filmData, statusData, resultData, printWaitTime, errorData):
        self.backCoverState, self.printerOperationFlg, self.printerErrFlg, self.printerOperationInfo = self.setStatusData(statusData) # unsigned char
        self.filmRemain, self.batteryRemain, self.chargeFlg = self.setFilmData(filmData) # unsigned char
        self.printWaitTime = printWaitTime # unsigned char
        self.printerErrType = errorData # int
        self.resultPrintRequest = PrinterResults(resultData) # PrinterResults

    def __str__(self):
        return f'Back cover open: {self.backCoverState}, battery remain: {self.batteryRemain}, charge flag: {self.chargeFlg}, film remain: {self.filmRemain}, print wait time: {self.printWaitTime}, printer error flag: {self.printerErrFlg}, printer error type: {self.printerErrType}, printer operation flag: {self.printerOperationFlg}, printer operation info: {self.printerOperationInfo}, result print request: {self.resultPrintRequest.name}'
    
    def setFilmData(self, byte):
        filmRemain = byte & 15
        batteryRemain = (byte >> 4) & 7
        chargeFlg = isKthBitSet(byte, 7)
        return filmRemain, batteryRemain, chargeFlg
    
    def setStatusData(self, byte):
        backCoverState = isKthBitSet(byte, 0)
        printerOperationFlg = isKthBitSet(byte, 1)
        printerErrFlg = isKthBitSet(byte, 2)
        printerOperationInfo = (byte >> 4) & 15
        return backCoverState, printerOperationFlg, printerErrFlg, printerOperationInfo

class PrintHistoryInfo():
    def __init__(self, totalPrintNum, totalEjectFCNum):
        self.totalPrintNum = totalPrintNum # int
        self.totalEjectFCNum = totalEjectFCNum # int

    def __str__(self):
        return f'Total number of prints: {self.totalPrintNum}, total number of ejects: {self.totalEjectFCNum}'

class SupportFunctionInfoResponse():
    def __init__(self, data):
        self.info = None
        type, = unpack_from('>B', data)
        self.type = SupportFunctionInfoType(type)
        if self.type == SupportFunctionInfoType.IMAGE_SUPPORT_INFO:
            width, height, picType, picOption, size = unpack_from('>HHBBI', data, 1)
            self.info = ImageSupportInfo(width, height, picType, picOption, size)
        elif self.type == SupportFunctionInfoType.BATTERY_INFO:
            batteryLevel, batteryCapacity, chargerType, chargerState = unpack_from('>BBBB', data, 1)
            self.info = BatteryInfo(batteryLevel, batteryCapacity, chargerType, chargerState)
        elif self.type == SupportFunctionInfoType.PRINTER_FUNCTION_INFO:
            filmData, statusData, resultData, printWaitTime, errorData = unpack_from('>BBBBI', data, 1)
            self.info = PrinterFunctionInfo(filmData, statusData, resultData, printWaitTime, errorData)
        elif self.type == SupportFunctionInfoType.PRINT_HISTORY_INFO:
            totalPrintNum, totalEjectFCNum = unpack_from('>II', data, 1)
            self.info = PrintHistoryInfo(totalPrintNum, totalEjectFCNum)

    def __str__(self):
        return f'Support function info type: {self.type.name}\n' + self.info.__str__()

class VoltageInfo():
    def __init__(self, batteryVoltage, printerTemperature):
        self.batteryVoltage = batteryVoltage # unsigned short
        self.printerTemperature = printerTemperature # unsigned short

    def __str__(self):
        return f'Battery voltage: {self.batteryVoltage}, printer temperature: {self.printerTemperature}'

class ColorInfo():
    def __init__(self, totalNumberOfPrintAttempts, batteryType, colorVariationInformation, withOrWithoutFilmPI):
        self.totalNumberOfPrintAttempts = totalNumberOfPrintAttempts # unsigned int
        self.batteryType = batteryType # unsigned short
        self.colorVariationInformation = CameraColor(colorVariationInformation) # unsigned short
        self.withOrWithoutFilmPI = withOrWithoutFilmPI # unsigned short

    def __str__(self):
        return f'Total number of print attempts: {self.totalNumberOfPrintAttempts}, battery type: {self.batteryType}, color variation: {self.colorVariationInformation.name}, with or without film PI: {self.withOrWithoutFilmPI}'

class AdditionalPrinterInfoResponse():
    def __init__(self, data):
        self.info = None
        type, = unpack_from('>B', data)
        self.type = AdditionalPrinterInfoType(type)
        if self.type == AdditionalPrinterInfoType.VOLTAGE_INFO:
            batteryVoltage, printerTemperature = unpack_from('>HH', data, 1)
            self.info = VoltageInfo(batteryVoltage, printerTemperature)
        elif self.type == AdditionalPrinterInfoType.COLOR_INFO:
            totalNumberOfPrintAttempts, batteryType, colorVariationInformation, withOrWithoutFilmPI = unpack_from('>IBBB', data, 1)
            self.info = ColorInfo(totalNumberOfPrintAttempts, batteryType, colorVariationInformation, withOrWithoutFilmPI)

    def __str__(self):
        return f'Additional printer info type: {self.type.name}\n' + self.info.__str__()

class AutoSleepSettingsResponse():
    def __init__(self, data):
        self.autoSleepTime1, self.autoSleepTime2, self.autoSleepTime3, self.autoSleepTime4 = unpack_from('>HHHH', data)

    def __str__(self):
        return f'Auto sleep time 1: {self.autoSleepTime1}, auto sleep time 2: {self.autoSleepTime2}, auto sleep time 3: {self.autoSleepTime3}, auto sleep time 4: {self.autoSleepTime4}'

class ImageTransferStartResponse():
    def __init__(self, data):
        self.frameSize, = unpack_from('>I', data)

    def __str__(self):
        return f'Frame size: {self.frameSize}'

class ImageFrameTransferResponse():
    def __init__(self, data):
        self.frameNumber, = unpack_from('>I', data)

    def __str__(self):
        return f'Frame number: {self.frameNumber}'

class ImagePrintResponse():
    def __init__(self, data):
        self.endTime, = unpack_from('>B', data)

    def __str__(self):
        return f'End time: {self.endTime}'

class LightCorrectInfoResponse():
    def __init__(self, data):
        printerHeadType, self.printingDateJudgeFlag, padding, self.year, self.month, self.day, self.rIntensity, self.gIntensity, self.bIntensity = unpack_from('>BBBHBBHHH', data)
        self.printerHeadType = PrinterMountedHeadType(printerHeadType)

    def __str__(self):
        return f'Printer head type: {self.printerHeadType.name}, date flag: {self.printingDateJudgeFlag}, year: {self.year}, month: {self.month}, day: {self.day}, R intensity: {self.rIntensity}, G intensity: {self.gIntensity}, B intensity: {self.bIntensity}'

# Communication

class InstaxConnection:
    def __init__(self, device_name, debug = False):

        self.serviceUUID = '70954782-2d83-473d-9e5f-81e1d02d5273'
        self.writeCharacteristicUUID = '70954783-2d83-473d-9e5f-81e1d02d5273'
        self.notifyCharacteristicUUID = '70954784-2d83-473d-9e5f-81e1d02d5273'
        
        self.device_name = device_name.upper()
        self.debug = debug

        self.client = None
        self.responseReceived = False
        self.response = None
    
    async def discover(self):
        devices = await BleakScanner.discover(5.0, return_adv = True)
        for device in devices:
            advertisement_data = devices[device][1]
            if(advertisement_data.local_name == self.device_name):
                return device
        return None

    async def connect(self):
        device = await self.discover()
        if device:
            print("Found Instax Link at address: %s" % (device))
            try:
                print("Attempting to connect...")
                self.client = BleakClient(device)
                await self.client.connect()
                print("Connected")
                await self.get_info()
                await self.client.start_notify(self.notifyCharacteristicUUID, self.response_callback)
                print("Callback set")
            except Exception as e:
                print("Failed to connect! %s" % e)
        else:
            raise Exception("Instax Link %s not found" % self.device_name)

    async def disconnect(self):
        try:
            print("Disconnecting...")
            await self.client.disconnect()
            print("Disconnected")
        except Exception as e:
            print("Failed to disconnect! %s" % e)

    async def get_info(self):
        try:
            manufacturerName = await self.client.read_gatt_char("00002a29-0000-1000-8000-00805f9b34fb")
            print("Manufacturer Name: %s" % manufacturerName.decode("ascii"))
        except:
            raise Exception("Failed to read Manufacturer Name")
        try:
            modelNumber = await self.client.read_gatt_char("00002a24-0000-1000-8000-00805f9b34fb")
            print("Model Number: %s" % modelNumber.decode("ascii"))
        except:
            raise Exception("Failed to read Model Number")
        try:
            serialNumber = await self.client.read_gatt_char("00002a25-0000-1000-8000-00805f9b34fb")
            print("Serial Number: %s" % serialNumber.decode("ascii"))
        except:
            raise Exception("Failed to read Serial Number")
        try:
            hardwareRevision = await self.client.read_gatt_char("00002a27-0000-1000-8000-00805f9b34fb")
            print("Hardware Revision: %s" % hardwareRevision.decode("ascii"))
        except:
            raise Exception("Failed to read Hardware Revision")
        try:
            firmwareRevision = await self.client.read_gatt_char("00002a26-0000-1000-8000-00805f9b34fb")
            print("Firmware Revision: %s" % firmwareRevision.decode("ascii"))
        except:
            raise Exception("Failed to read Firmware Revision")
        try:
            softwareRevision = await self.client.read_gatt_char("00002a28-0000-1000-8000-00805f9b34fb")
            print("Software Revision: %s" % softwareRevision.decode("ascii"))
        except:
            raise Exception("Failed to read Software Revision")
        try:
            systemId = await self.client.read_gatt_char("00002a23-0000-1000-8000-00805f9b34fb")
            print("System ID: " + "".join("{:02x} ".format(x) for x in systemId))
        except:
            raise Exception("Failed to read System ID")
        try:
            ieee = await self.client.read_gatt_char("00002a2a-0000-1000-8000-00805f9b34fb")
            print("IEEE Regulatory Certification: " + "".join("{:02x} ".format(x) for x in ieee))
        except:
            raise Exception("Failed to read IEEE Regulatory Certification")
        try:
            pnpId = await self.client.read_gatt_char("00002a50-0000-1000-8000-00805f9b34fb")
            print("PnP ID:  " + "".join("{:02x} ".format(x) for x in pnpId))
        except:
            raise Exception("Failed to read PnP ID")

    async def send_command(self, payload):
        maxPacketSize = 182
        numberOfPackets = math.ceil(len(payload) / maxPacketSize)
        for packetIndex in range(numberOfPackets):
            packet = payload[packetIndex * maxPacketSize:packetIndex * maxPacketSize + maxPacketSize]
            if self.debug:
                print("Sending payload %s" % packet.hex(' ', 1))
            await self.client.write_gatt_char(self.writeCharacteristicUUID, packet, False)
        while self.responseReceived == False:
            await asyncio.sleep(0.1)
        self.responseReceived = False
        if self.debug:
            print(self.response)
        return self.response
    
    def response_callback(self, characteristic, payload):
        response = Response(payload)
        if self.debug:
            print("Received response %s" % response)
        if response.valid:
            sid = response.message.sid
            if sid == SID.SUPPORT_FUNCTION_AND_VERSION_INFO:
                self.response = SupportFunctionaAndVersionInfoResponse(response.message.data)
            elif sid == SID.DEVICE_INFO_SERVICE:
                self.response = DeviceInfoResponse(response.message.data)
            elif sid == SID.SUPPORT_FUNCTION_INFO:
                self.response = SupportFunctionInfoResponse(response.message.data)
            elif sid == SID.ADDITIONAL_PRINTER_INFO:
                self.response = AdditionalPrinterInfoResponse(response.message.data)
            elif sid == SID.PRINTER_HEAD_LIGHT_CORRECT_INFO:
                self.response = LightCorrectInfoResponse(response.message.data)
            elif sid == SID.AUTO_SLEEP_SETTINGS:
                self.response = AutoSleepSettingsResponse(response.message.data)
            elif sid == SID.PRINT_IMAGE_DOWNLOAD_START:
                self.response = ImageTransferStartResponse(response.message.data)
            elif sid == SID.PRINT_IMAGE_DOWNLOAD_DATA:
                self.response = ImageFrameTransferResponse(response.message.data)
            elif sid == SID.PRINT_IMAGE_DOWNLOAD_END:
                self.response = None
            elif sid == SID.PRINT_IMAGE:
                self.response = ImagePrintResponse(response.message.data)
            else:
                print("Unsupported SID %s!" % sid.name)
                self.response = None
        else:
            print("Invalid response!")
        self.responseReceived = True
    
    async def request_version_info(self):
        return await self.send_command(SupportFunctionaAndVersionInfoRequest().message.get_payload())
    
    async def request_device_info_model(self):
        return await self.send_command(DeviceInfoRequest(DeviceInfoType.MODEL_NUMBER).message.get_payload())
    
    async def request_device_info_serial(self):
        return await self.send_command(DeviceInfoRequest(DeviceInfoType.SERIAL_NUMBER).message.get_payload())
    
    async def request_device_info_hw(self):
        return await self.send_command(DeviceInfoRequest(DeviceInfoType.HW_REVISION).message.get_payload())
    
    async def request_function_info_image(self):
        return await self.send_command(SupportFunctionInfoRequest(SupportFunctionInfoType.IMAGE_SUPPORT_INFO).message.get_payload())
    
    async def request_function_info_battery(self):
        return await self.send_command(SupportFunctionInfoRequest(SupportFunctionInfoType.BATTERY_INFO).message.get_payload())
    
    async def request_function_info_printer_function(self):
        return await self.send_command(SupportFunctionInfoRequest(SupportFunctionInfoType.PRINTER_FUNCTION_INFO).message.get_payload())
    
    async def request_function_info_print_history(self):
        return await self.send_command(SupportFunctionInfoRequest(SupportFunctionInfoType.PRINT_HISTORY_INFO).message.get_payload())
    
    async def request_printer_info_voltage(self):
        return await self.send_command(AdditionalPrinterInfoRequest(AdditionalPrinterInfoType.VOLTAGE_INFO).message.get_payload())

    async def request_printer_info_color(self):
        return await self.send_command(AdditionalPrinterInfoRequest(AdditionalPrinterInfoType.COLOR_INFO).message.get_payload())
    
    async def request_request_head_calibration_info(self):
        return await self.send_command(LightCorrectInfoRequest().message.get_payload())

    async def request_sleep_settings_extend(self, time1, time2, time3, time4):
        return await self.send_command(AutoSleepSettingsRequest(AutoSleepSettingsMode.EXTEND_CURRENT_SLEEP_SETTING, time1, time2, time3, time4).message.get_payload())
    
    async def request_image_transfer_start(self, pictureType, picturePrintOption, size):
        return await self.send_command(ImageTransferStartRequest(pictureType, picturePrintOption, size).message.get_payload())
    
    async def request_image_frame_transfer(self, frameNumber, frameData):
        return await self.send_command(ImageFrameTransferRequest(frameNumber, frameData).message.get_payload())
    
    async def request_image_transfer_end(self):
        return await self.send_command(ImageTransferEndRequest().message.get_payload())
    
    async def request_print(self):
        return await self.send_command(ImagePrintRequest().message.get_payload())

# Printer

class InstaxPrinter:
    def __init__(self, device_name, image_path = None, debug = False):
        self.debug = debug
        self.connection = InstaxConnection(device_name, debug)
        
        self.model = ''
        self.serial = ''
        self.hwRevision = ''

        self.imageWidth = 0
        self.imageHeight = 0
        self.maxImageSize = 0
        self.picType = PictureType.PICINF_PICTYPE_NONE

        self.batteryLevel = 0
        self.remainingPictures = 0
        self.printerStatus = PrinterResults.NORMAL_TERMINATION

        self.imagePath = image_path
        self.imageFrameSize = 0

    def __str__(self):
        return f'Model: {self.model}, battery level: {self.batteryLevel}, remaining pictures: {self.remainingPictures}, status: {self.printerStatus.name}'
    
    async def connect(self):
        await self.connection.connect()
        self.set_device_info(await self.connection.request_device_info_model())
        self.set_device_info(await self.connection.request_device_info_serial())
        self.set_device_info(await self.connection.request_device_info_hw())
        self.set_function_info(await self.connection.request_function_info_image())
        self.set_function_info(await self.connection.request_function_info_printer_function())
    
    async def disconnect(self):
        await self.connection.disconnect()
    
    def set_device_info(self, data):
        if data.type == DeviceInfoType.MODEL_NUMBER:
            self.model = data.value
        elif data.type == DeviceInfoType.SERIAL_NUMBER:
            self.serial = data.value
        elif data.type == DeviceInfoType.HW_REVISION:
            self.hwRevision = data.value

    def set_function_info(self, data):
        if data.type == SupportFunctionInfoType.IMAGE_SUPPORT_INFO:
            self.imageWidth = data.info.width
            self.imageHeight = data.info.height
            self.maxImageSize = data.info.size
            self.picType = data.info.picType
        elif data.type == SupportFunctionInfoType.PRINTER_FUNCTION_INFO:
            self.batteryLevel = data.info.batteryRemain
            self.remainingPictures = data.info.filmRemain
            self.printerStatus = data.info.resultPrintRequest
    
    def set_image_transfer_info(self, data):
        self.imageFrameSize = data.frameSize

    def check_image(self):
        image = Image.open(self.imagePath)
        if image.width == self.imageWidth and image.height == self.imageHeight and image.format == 'JPEG' and os.path.getsize(self.imagePath) <= self.maxImageSize:
            return True
        return False
    
    def prepare_image(self): # TODO: resize and compress according to requirements, if needed
        image = Image.open(self.imagePath)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        return img_byte_arr.getvalue()
    
    async def print_image(self):
        if self.check_image():
            with open(self.imagePath, 'rb') as image:
                img_byte_arr = image.read()
                if self.debug:
                    print("Image size %i" % len(img_byte_arr))
                self.set_image_transfer_info(await self.connection.request_image_transfer_start(PictureType.PICINF_PICTYPE_JPEG, PicturePrintOption.PICINF_PICOP_NONE, len(img_byte_arr)))
                frames = slice_image(img_byte_arr, self.imageFrameSize)
                if self.debug:
                    print("Requested frame size %i, prepared frame size %i, number of frames %i" % (self.imageFrameSize, len(frames[0]), len(frames)))
            for i in range(len(frames)):
                frameNumber = (await self.connection.request_image_frame_transfer(i, frames[i])).frameNumber
                print("Transferred frame number %i of %i" % (frameNumber + 1, len(frames)))
            await self.connection.request_image_transfer_end()
            endTime = await self.connection.request_print()
            print("Printing... Estimated time required %i seconds" % endTime)
            self.set_function_info(await self.connection.request_function_info_printer_function())
            while self.printerStatus == PrinterResults.PRINTER_PROCESSING:
                self.set_function_info(await self.connection.request_function_info_printer_function())
                await asyncio.sleep(1.0)
            print("Print process completed with status %s" % self.printerStatus.name)
        else:
            print("The provided image cannot be printed! It must be a JPG file with height %i, width %i and maximum size %i KB" % (self.imageHeight, self.imageWidth, self.maxImageSize))

# main

async def main(args={}):
    try:
        instax = InstaxPrinter(**args)
        await instax.connect()
        print(instax)
        await instax.print_image()
        await instax.disconnect()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "Utility to print a JPG image to an InstaxLink printer")
    parser.add_argument('-n', '--device-name', help = 'Device name, format INSTAX-xxxxxxxx(IOS)') # INSTAX-20189264(IOS)
    parser.add_argument('-i', '--image-path', help = 'Path to the image file')
    parser.add_argument('-d', '--debug', action = 'store_true')
    args = parser.parse_args()

    asyncio.run(main(vars(args)))