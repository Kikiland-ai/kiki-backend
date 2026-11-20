"""Bounded virtual observations. No LLM decides numerical correctness."""
import math


class DeclarativeBehavior:
    """Default adapter for packs whose checkpoints are declarative actions."""
    def observations(self, pack, apparatus):
        return {"model": "declarative/v1", "virtual": True, "readings": {}, "traces": {}}

    def expected_measurement(self, pack, apparatus, rule):
        return rule["value"]


class DsbScBehavior:
    def expected_measurement(self, pack, apparatus, rule):
        observation = self.observations(pack, apparatus)
        if not observation["receiver_connected"] or not observation["display_stable"]:
            raise ValueError("Connect the receiver and stabilise the display before measuring")
        if rule["other"] not in observation["readings"]:
            raise ValueError("Unsupported model reading")
        return observation["readings"][rule["other"]]

    def observations(self, pack, apparatus):
        c = apparatus["controls"]
        edges = apparatus["connections"]
        def wired(a, b):
            return [a, b] in edges
        powered = c["trainer.power"] is True
        tx = powered and wired("source.message", "modulator.message") and wired("source.carrier", "modulator.carrier")
        rx = tx and wired("modulator.output", "detector.input") and wired("source.carrier", "detector.reference")
        fm, fc = c["source.message_frequency"], c["source.carrier_frequency"]
        leak = c["modulator.null"]
        stable = c["scope.trigger"] == "auto"
        points = 1024
        times = [i * .002 / (points - 1) for i in range(points)]
        message = [math.sin(2 * math.pi * fm * t) for t in times]
        carrier = [math.cos(2 * math.pi * fc * t) for t in times]
        modulated = [(m + leak) * a if tx else 0.0 for m, a in zip(message, carrier)]
        # Ideal unit-amplitude coherent reference and unity receiver gain:
        # LPF{m(t) cos(wc*t)^2} = 0.5*m(t). A residual carrier gives a DC term.
        recovered = [.5 * (m + leak) if rx else 0.0 for m in message]
        return {
            "model": "dsb-sc-ideal/v1", "virtual": True,
            "assumptions": ["Unit peak message and carrier amplitudes (1 V)",
                            "Ideal synchronous detector and ideal low-pass filter; unity recovery gain",
                            "Shared coherent reference; phase adjustment is not a trainer control",
                            "Null is a pedagogical residual-carrier coefficient, not a calibrated dial"],
            "transmitter_connected": tx, "receiver_connected": rx, "display_stable": stable,
            "readings": {"message_frequency_hz": fm if powered else 0,
                         "recovered_frequency_hz": fm if rx else 0,
                         "recovered_peak_v": .5 if rx else 0,
                         "residual_carrier_coefficient": leak},
            "spectrum": {"sidebands_hz": [fc - fm, fc + fm] if tx else [],
                         "carrier_suppressed": tx and abs(leak) <= .02},
            "traces": {"time_s": times, "message_v": message if powered else [0.0] * points,
                       "dsb_sc_v": modulated, "recovered_v": recovered},
        }


ADAPTERS = {"declarative/v1": DeclarativeBehavior, "dsb-sc-ideal/v1": DsbScBehavior}
