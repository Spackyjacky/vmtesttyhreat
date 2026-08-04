import Foundation
import CoreBluetooth

/// Manages a Bluetooth Low Energy connection to a generic ESC/POS thermal receipt printer.
/// Discovers any nearby peripheral and, once connected, finds a writable characteristic to
/// stream raw ESC/POS command bytes to. This works with the majority of budget BLE 58/80mm
/// POS printers without needing a vendor-specific SDK or exact service/characteristic UUIDs.
@MainActor
final class BluetoothPrinterManager: NSObject, ObservableObject {
    struct DiscoveredPrinter: Identifiable, Equatable {
        let id: UUID
        let name: String
        let peripheral: CBPeripheral

        static func == (lhs: DiscoveredPrinter, rhs: DiscoveredPrinter) -> Bool { lhs.id == rhs.id }
    }

    enum ConnectionState: Equatable {
        case disconnected
        case connecting
        case connected
        case failed(String)
    }

    @Published var isBluetoothPoweredOn = false
    @Published var isScanning = false
    @Published var discoveredPrinters: [DiscoveredPrinter] = []
    @Published var connectedPrinter: DiscoveredPrinter?
    @Published var connectionState: ConnectionState = .disconnected
    @Published var lastError: String?

    private var centralManager: CBCentralManager!
    private var writeCharacteristic: CBCharacteristic?
    private let maxWriteLength = 20

    override init() {
        super.init()
        centralManager = CBCentralManager(delegate: self, queue: nil)
    }

    func startScan() {
        guard isBluetoothPoweredOn else { return }
        discoveredPrinters.removeAll()
        isScanning = true
        centralManager.scanForPeripherals(withServices: nil, options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
    }

    func stopScan() {
        centralManager.stopScan()
        isScanning = false
    }

    func connect(to printer: DiscoveredPrinter) {
        stopScan()
        connectionState = .connecting
        printer.peripheral.delegate = self
        centralManager.connect(printer.peripheral, options: nil)
    }

    func disconnect() {
        guard let peripheral = connectedPrinter?.peripheral else { return }
        centralManager.cancelPeripheralConnection(peripheral)
    }

    /// Attempts to reconnect to a previously paired printer by its identifier, without scanning.
    func reconnectIfPossible(savedIdentifier: String?) {
        guard let idString = savedIdentifier, let uuid = UUID(uuidString: idString) else { return }
        let peripherals = centralManager.retrievePeripherals(withIdentifiers: [uuid])
        guard let peripheral = peripherals.first else { return }
        connect(to: DiscoveredPrinter(id: peripheral.identifier, name: peripheral.name ?? "Printer", peripheral: peripheral))
    }

    func send(_ bytes: [UInt8]) {
        guard let peripheral = connectedPrinter?.peripheral, let characteristic = writeCharacteristic else {
            lastError = "No printer connected."
            return
        }
        let data = Data(bytes)
        var offset = 0
        let writeType: CBCharacteristicWriteType = characteristic.properties.contains(.write) ? .withResponse : .withoutResponse
        while offset < data.count {
            let end = min(offset + maxWriteLength, data.count)
            let chunk = data.subdata(in: offset..<end)
            peripheral.writeValue(chunk, for: characteristic, type: writeType)
            offset = end
        }
    }

    func openCashDrawer() {
        send(ESCPOS.openCashDrawer())
    }

    func printReceipt(bytes: [UInt8]) {
        send(bytes)
    }
}

extension BluetoothPrinterManager: CBCentralManagerDelegate {
    nonisolated func centralManagerDidUpdateState(_ central: CBCentralManager) {
        let poweredOn = central.state == .poweredOn
        Task { @MainActor in self.isBluetoothPoweredOn = poweredOn }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String: Any], rssi RSSI: NSNumber) {
        guard let name = peripheral.name, !name.isEmpty else { return }
        let discovered = DiscoveredPrinter(id: peripheral.identifier, name: name, peripheral: peripheral)
        Task { @MainActor in
            if !self.discoveredPrinters.contains(discovered) {
                self.discoveredPrinters.append(discovered)
            }
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        peripheral.discoverServices(nil)
    }

    nonisolated func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        let message = error?.localizedDescription ?? "Failed to connect"
        Task { @MainActor in self.connectionState = .failed(message) }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        Task { @MainActor in
            self.connectedPrinter = nil
            self.writeCharacteristic = nil
            self.connectionState = .disconnected
        }
    }
}

extension BluetoothPrinterManager: CBPeripheralDelegate {
    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let services = peripheral.services else { return }
        for service in services {
            peripheral.discoverCharacteristics(nil, for: service)
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard let characteristics = service.characteristics else { return }
        for characteristic in characteristics where characteristic.properties.contains(.write) || characteristic.properties.contains(.writeWithoutResponse) {
            let name = peripheral.name ?? "Printer"
            let identifier = peripheral.identifier
            Task { @MainActor in
                self.writeCharacteristic = characteristic
                self.connectedPrinter = DiscoveredPrinter(id: identifier, name: name, peripheral: peripheral)
                self.connectionState = .connected
            }
            break
        }
    }
}
