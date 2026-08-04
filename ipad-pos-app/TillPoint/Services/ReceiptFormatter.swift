import Foundation

enum ReceiptFormatter {
    static func escposReceipt(for sale: Sale, settings: AppSettings, openDrawer: Bool) -> [UInt8] {
        var bytes: [UInt8] = []
        bytes += ESCPOS.initializePrinter
        bytes += ESCPOS.alignCenter
        bytes += ESCPOS.boldOn
        bytes += ESCPOS.doubleHeightWidthOn
        bytes += ESCPOS.line(settings.storeName)
        bytes += ESCPOS.normalText
        bytes += ESCPOS.boldOff
        if !settings.addressLine1.isEmpty { bytes += ESCPOS.line(settings.addressLine1) }
        if !settings.addressLine2.isEmpty { bytes += ESCPOS.line(settings.addressLine2) }
        if !settings.phoneNumber.isEmpty { bytes += ESCPOS.line(settings.phoneNumber) }
        bytes += ESCPOS.lineFeed(1)

        bytes += ESCPOS.alignLeft
        bytes += ESCPOS.line("Receipt #: \(sale.receiptNumber)")
        bytes += ESCPOS.line(dateFormatter.string(from: sale.date))
        if let op = sale.operatorName, !op.isEmpty { bytes += ESCPOS.line("Operator: \(op)") }
        bytes += ESCPOS.line(String(repeating: "-", count: 32))

        for item in sale.lineItems ?? [] {
            let qtyPrice = "\(item.quantity) x \(CurrencyFormatter.string(fromCents: item.unitPriceCents, currencyCode: settings.currencyCode))"
            let total = CurrencyFormatter.string(fromCents: item.lineTotalCents, currencyCode: settings.currencyCode)
            bytes += ESCPOS.line(item.productName)
            bytes += ESCPOS.line(padLine(left: qtyPrice, right: total))
        }

        bytes += ESCPOS.line(String(repeating: "-", count: 32))
        bytes += ESCPOS.line(padLine(left: "Subtotal", right: CurrencyFormatter.string(fromCents: sale.subtotalCents, currencyCode: settings.currencyCode)))
        bytes += ESCPOS.line(padLine(left: "Tax", right: CurrencyFormatter.string(fromCents: sale.taxCents, currencyCode: settings.currencyCode)))
        bytes += ESCPOS.boldOn
        bytes += ESCPOS.line(padLine(left: "TOTAL", right: CurrencyFormatter.string(fromCents: sale.totalCents, currencyCode: settings.currencyCode)))
        bytes += ESCPOS.boldOff
        bytes += ESCPOS.line(padLine(left: "Paid (\(sale.paymentMethod.displayName))", right: CurrencyFormatter.string(fromCents: sale.totalCents, currencyCode: settings.currencyCode)))
        if let tendered = sale.cashTenderedCents {
            bytes += ESCPOS.line(padLine(left: "Tendered", right: CurrencyFormatter.string(fromCents: tendered, currencyCode: settings.currencyCode)))
        }
        if let change = sale.changeDueCents, change > 0 {
            bytes += ESCPOS.line(padLine(left: "Change", right: CurrencyFormatter.string(fromCents: change, currencyCode: settings.currencyCode)))
        }

        bytes += ESCPOS.lineFeed(1)
        bytes += ESCPOS.alignCenter
        bytes += ESCPOS.barcodeCode128(sale.receiptNumber)
        bytes += ESCPOS.lineFeed(1)
        if !settings.receiptFooter.isEmpty {
            bytes += ESCPOS.line(settings.receiptFooter)
        }
        bytes += ESCPOS.lineFeed(3)
        bytes += ESCPOS.cutPaperFull
        if openDrawer {
            bytes += ESCPOS.openCashDrawer()
        }
        return bytes
    }

    static func plainTextReceipt(for sale: Sale, settings: AppSettings) -> String {
        var lines: [String] = []
        lines.append(settings.storeName)
        if !settings.addressLine1.isEmpty { lines.append(settings.addressLine1) }
        lines.append("Receipt #\(sale.receiptNumber)  \(dateFormatter.string(from: sale.date))")
        lines.append(String(repeating: "-", count: 32))
        for item in sale.lineItems ?? [] {
            lines.append("\(item.quantity) x \(item.productName) \u{2014} \(CurrencyFormatter.string(fromCents: item.lineTotalCents, currencyCode: settings.currencyCode))")
        }
        lines.append(String(repeating: "-", count: 32))
        lines.append("Subtotal: \(CurrencyFormatter.string(fromCents: sale.subtotalCents, currencyCode: settings.currencyCode))")
        lines.append("Tax: \(CurrencyFormatter.string(fromCents: sale.taxCents, currencyCode: settings.currencyCode))")
        lines.append("Total: \(CurrencyFormatter.string(fromCents: sale.totalCents, currencyCode: settings.currencyCode))")
        lines.append("")
        lines.append(settings.receiptFooter)
        return lines.joined(separator: "\n")
    }

    private static func padLine(left: String, right: String, width: Int = 32) -> String {
        let space = width - left.count - right.count
        if space <= 1 { return left + " " + right }
        return left + String(repeating: " ", count: space) + right
    }

    private static let dateFormatter: DateFormatter = {
        let df = DateFormatter()
        df.dateStyle = .medium
        df.timeStyle = .short
        return df
    }()
}
