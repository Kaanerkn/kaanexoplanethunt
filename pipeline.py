import pandas as pd

def run_pipeline(file_path: str) -> pd.DataFrame:
    """
    Main exoplanet candidate filtering pipeline.

    Parameters
    ----------
    file_path : str
        Input CSV/Excel path (TESS / NASA catalog).

    Returns
    -------
    pd.DataFrame
        Filtered dataframe with scoring and class labels.
    """
    df = pd.read_csv(file_path)

    # TODO: Buraya githubkaanexo.ipynb içindeki kodun gelecek.
    # Örneğin:
    # df = clean_data(df)
    # df = apply_physical_filters(df)
    # df = apply_scoring(df)
    # df = add_class_labels(df)

    return df
  
