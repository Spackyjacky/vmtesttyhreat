import XCTest
@testable import TillPoint

final class EscPosBuilderTests: XCTestCase {
    func testOpenCashDrawerCommandShape() {
        let bytes = ESCPOS.openCashDrawer(pin: 0, onMs: 25, offMs: 250)
        XCTAssertEqual(bytes.count, 5)
        XCTAssertEqual(bytes[0], ESCPOS.ESC)
        XCTAssertEqual(bytes[1], 0x70)
        XCTAssertEqual(bytes[2], 0)
    }

    func testBarcodeCode128IncludesLengthPrefixedPayload() {
        let bytes = ESCPOS.barcodeCode128("123456")
        // Ends with GS k 73 <len> "{B123456"
        let payload = Array("{B123456".utf8)
        XCTAssertEqual(Array(bytes.suffix(payload.count)), payload)
    }

    func testLineAppendsLineFeed() {
        let bytes = ESCPOS.line("hello")
        XCTAssertEqual(bytes.last, ESCPOS.LF)
    }
}
