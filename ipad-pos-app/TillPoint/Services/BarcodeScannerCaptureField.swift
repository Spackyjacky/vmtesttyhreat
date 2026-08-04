import SwiftUI
import UIKit

/// An invisible, always-focused text field that captures input from Bluetooth (or USB)
/// barcode scanners operating as HID "keyboard wedge" devices — the standard behavior
/// for the vast majority of barcode scanners on iOS/iPadOS, requiring no pairing code.
/// Rapid keystrokes terminated by Enter/Return are treated as a completed scan.
struct BarcodeScannerCaptureField: UIViewRepresentable {
    var onScan: (String) -> Void
    var isActive: Bool = true

    func makeUIView(context: Context) -> UnderlyingTextField {
        let field = UnderlyingTextField()
        field.delegate = context.coordinator
        field.autocorrectionType = .no
        field.autocapitalizationType = .none
        field.spellCheckingType = .no
        field.tintColor = .clear
        field.textColor = .clear
        field.backgroundColor = .clear
        return field
    }

    func updateUIView(_ uiView: UnderlyingTextField, context: Context) {
        if isActive {
            if !uiView.isFirstResponder {
                DispatchQueue.main.async { uiView.becomeFirstResponder() }
            }
        } else {
            uiView.resignFirstResponder()
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator(onScan: onScan) }

    final class UnderlyingTextField: UITextField {
        override var canBecomeFirstResponder: Bool { true }
        override func canPerformAction(_ action: Selector, withSender sender: Any?) -> Bool { false }
    }

    final class Coordinator: NSObject, UITextFieldDelegate {
        let onScan: (String) -> Void
        private var buffer = ""
        private var lastKeystroke: Date = .distantPast

        init(onScan: @escaping (String) -> Void) {
            self.onScan = onScan
        }

        func textField(_ textField: UITextField, shouldChangeCharactersIn range: NSRange, replacementString string: String) -> Bool {
            let now = Date()
            let interval = now.timeIntervalSince(lastKeystroke)
            lastKeystroke = now

            if string == "\n" {
                submitIfLooksLikeScan()
                textField.text = ""
                return false
            }

            if interval > 0.4 {
                buffer = ""
            }
            buffer += string
            return true
        }

        func textFieldShouldReturn(_ textField: UITextField) -> Bool {
            submitIfLooksLikeScan()
            textField.text = ""
            return false
        }

        private func submitIfLooksLikeScan() {
            let code = buffer.trimmingCharacters(in: .whitespacesAndNewlines)
            buffer = ""
            guard code.count >= 3 else { return }
            onScan(code)
        }
    }
}
