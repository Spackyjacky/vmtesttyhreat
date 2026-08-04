import SwiftUI

/// On-screen numeric keypad for entering cash tendered, plus quick "notes handed
/// over" buttons that add to the running total — mirrors how a physical till works.
struct CashKeypadView: View {
    @Binding var amountCents: Int
    let totalCents: Int
    let currencyCode: String

    private let maxCents = 100_000_000 // cap at 1,000,000.00 to avoid runaway typing

    private var quickAmounts: [Int] {
        switch currencyCode {
        case "USD": return [500, 1000, 2000, 5000, 10000]
        default: return [500, 1000, 2000, 5000]
        }
    }

    var body: some View {
        VStack(spacing: 12) {
            Text(CurrencyFormatter.string(fromCents: amountCents, currencyCode: currencyCode))
                .font(.system(size: 32, weight: .bold, design: .rounded))
                .frame(maxWidth: .infinity, alignment: .trailing)
                .padding(.horizontal, 8)
                .lineLimit(1)
                .minimumScaleFactor(0.5)

            HStack(spacing: 8) {
                quickButton("Exact") { amountCents = totalCents }
                ForEach(quickAmounts, id: \.self) { value in
                    quickButton(CurrencyFormatter.string(fromCents: value, currencyCode: currencyCode)) {
                        amountCents = min(maxCents, amountCents + value)
                    }
                }
            }

            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 3), spacing: 8) {
                ForEach(1...9, id: \.self) { digit in
                    keypadButton("\(digit)") { appendDigit(digit) }
                }
                keypadButton("C", tint: .red) { amountCents = 0 }
                keypadButton("0") { appendDigit(0) }
                keypadButton("\u{232B}", tint: .orange) { amountCents /= 10 }
            }
        }
    }

    private func appendDigit(_ digit: Int) {
        guard amountCents < maxCents / 10 else { return }
        amountCents = amountCents * 10 + digit
    }

    private func quickButton(_ label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.subheadline.bold())
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
        }
        .buttonStyle(.bordered)
    }

    private func keypadButton(_ label: String, tint: Color = .accentColor, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.title2.weight(.semibold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
        }
        .buttonStyle(.bordered)
        .tint(tint)
    }
}
