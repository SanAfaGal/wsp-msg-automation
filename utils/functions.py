from pandas import DataFrame


def add_phone_column(df: DataFrame) -> DataFrame:
    """
    Add 'TELEFONO' column by combining 'INDICATIVO' and 'CONTACTO' columns.

    Args:
        df: DataFrame containing the original data.

    Returns:
        DataFrame with 'TELEFONO' column added.

    Raises:
        KeyError: If required columns are missing.
        ValueError: If data types are invalid.
    """
    required_columns = ['INDICATIVO', 'CONTACTO']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise KeyError(f"Missing required columns: {missing_columns}")

    try:
        df['TELEFONO'] = df['INDICATIVO'].astype(str) + ' ' + df['CONTACTO'].astype(str)
        return df.drop(columns=required_columns)
    except Exception as e:
        raise ValueError(f"Error processing phone numbers: {str(e)}")
