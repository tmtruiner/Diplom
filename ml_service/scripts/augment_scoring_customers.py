import argparse

from src.scoring_augmentation import (
    DEFAULT_TARGET_SCORING_CUSTOMERS,
    augment_scoring_customers,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic scoring_batch customers for demo volume."
    )
    parser.add_argument(
        "--target-count",
        type=int,
        default=DEFAULT_TARGET_SCORING_CUSTOMERS,
        help="Target number of scoring_batch customers after augmentation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible synthetic records.",
    )
    args = parser.parse_args()

    result = augment_scoring_customers(
        target_count=args.target_count,
        seed=args.seed,
    )

    print(f"Existing scoring customers: {result.existing_scoring_customers}")
    print(f"Inserted synthetic customers: {result.inserted_customers}")
    print(f"Final scoring customers: {result.final_scoring_customers}")


if __name__ == "__main__":
    main()
