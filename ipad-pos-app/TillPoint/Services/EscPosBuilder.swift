import Foundation

/// Byte-level command builder for the ESC/POS protocol used by the vast majority
/// of thermal receipt printers (including generic BLE 58mm/80mm printers).
enum ESCPOS {
    static let ESC: UInt8 = 0x1B
    static let GS: UInt8 = 0x1D
    static let LF: UInt8 = 0x0A

    static var initializePrinter: [UInt8] { [ESC, 0x40] }

    static var alignLeft: [UInt8] { [ESC, 0x61, 0x00] }
    static var alignCenter: [UInt8] { [ESC, 0x61, 0x01] }
    static var alignRight: [UInt8] { [ESC, 0x61, 0x02] }

    static var boldOn: [UInt8] { [ESC, 0x45, 0x01] }
    static var boldOff: [UInt8] { [ESC, 0x45, 0x00] }

    static var doubleHeightWidthOn: [UInt8] { [GS, 0x21, 0x11] }
    static var normalText: [UInt8] { [GS, 0x21, 0x00] }

    static var underlineOn: [UInt8] { [ESC, 0x2D, 0x01] }
    static var underlineOff: [UInt8] { [ESC, 0x2D, 0x00] }

    static func lineFeed(_ lines: Int = 1) -> [UInt8] {
        Array(repeating: LF, count: max(1, lines))
    }

    static func text(_ string: String) -> [UInt8] { Array(string.utf8) }

    static func line(_ string: String) -> [UInt8] { text(string) + [LF] }

    static var cutPaperFull: [UInt8] { [GS, 0x56, 0x00] }
    static var cutPaperPartial: [UInt8] { [GS, 0x56, 0x01] }

    /// Fires the drawer-kick pulse on the printer's RJ11 drawer port.
    /// pin 0 = drawer 1 (the common default wiring), pin 1 = drawer 2.
    static func openCashDrawer(pin: UInt8 = 0, onMs: Int = 25, offMs: Int = 250) -> [UInt8] {
        let t1 = UInt8(clamping: onMs / 2)
        let t2 = UInt8(clamping: offMs / 2)
        return [ESC, 0x70, pin, t1, t2]
    }

    /// Prints a CODE128 barcode (Code Set B) with human-readable text underneath.
    static func barcodeCode128(_ content: String, height: UInt8 = 80, width: UInt8 = 2) -> [UInt8] {
        var bytes: [UInt8] = []
        bytes += [GS, 0x68, height]       // GS h — barcode height
        bytes += [GS, 0x77, width]        // GS w — barcode module width
        bytes += [GS, 0x48, 0x02]         // GS H — print HRI text below barcode
        let data = "{B" + content         // "{B" selects CODE128 Code Set B
        let dataBytes = Array(data.utf8)
        bytes += [GS, 0x6B, 0x49, UInt8(clamping: dataBytes.count)] + dataBytes // GS k, m=73 (CODE128)
        return bytes
    }
}
