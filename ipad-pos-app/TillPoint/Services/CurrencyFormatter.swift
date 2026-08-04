import Foundation

enum CurrencyFormatter {
    static func string(fromCents cents: Int, currencyCode: String = "GBP") -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = currencyCode
        let amount = Decimal(cents) / 100
        return formatter.string(from: amount as NSDecimalNumber) ?? "\(currencyCode) \(amount)"
    }
}
