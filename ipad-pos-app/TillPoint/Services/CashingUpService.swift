import Foundation

struct CashingUpSummary {
    let session: TillSession
    let transactionCount: Int
    let cashTotalCents: Int
    let cardTotalCents: Int
    let otherTotalCents: Int

    var grossTotalCents: Int { cashTotalCents + cardTotalCents + otherTotalCents }
    var expectedCashCents: Int { session.openingFloatCents + cashTotalCents }
}

enum CashingUpService {
    /// Summarizes completed sales that fall within a till session's open window
    /// (from open to close, or to now if the session is still open).
    static func summary(for session: TillSession, sales: [Sale]) -> CashingUpSummary {
        let windowEnd = session.closedAt ?? .distantFuture
        let sessionSales = sales.filter {
            $0.status == .completed && $0.date >= session.openedAt && $0.date <= windowEnd
        }
        let cash = sessionSales.filter { $0.paymentMethod == .cash }.reduce(0) { $0 + $1.totalCents }
        let card = sessionSales.filter { $0.paymentMethod == .card }.reduce(0) { $0 + $1.totalCents }
        let other = sessionSales.filter { $0.paymentMethod == .other }.reduce(0) { $0 + $1.totalCents }
        return CashingUpSummary(
            session: session,
            transactionCount: sessionSales.count,
            cashTotalCents: cash,
            cardTotalCents: card,
            otherTotalCents: other
        )
    }

    static func varianceLabel(_ varianceCents: Int, currencyCode: String) -> String {
        let formatted = CurrencyFormatter.string(fromCents: abs(varianceCents), currencyCode: currencyCode)
        if varianceCents == 0 { return "Exact (\(formatted))" }
        return varianceCents > 0 ? "+\(formatted) over" : "-\(formatted) short"
    }
}
