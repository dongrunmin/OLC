"""Run all five health analyses with the same configurations as the entry scripts."""
import pandas as pd
from health_utils import FILES, analysis, arguments, save_and_print


def main():
    args = arguments(__doc__)
    parts, audits = [], []
    for name, filename in FILES.items():
        result = analysis(name, args.data)
        save_and_print(result, filename, args.output_dir)
        audits.extend(result.attrs["sample_audit"])
        result.attrs.clear()
        parts.append(result)
    combined = pd.concat(parts, ignore_index=True)
    combined.attrs["sample_audit"] = audits
    save_and_print(combined, "health_models_all_results.csv", args.output_dir)


if __name__ == "__main__":
    main()
