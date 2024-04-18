import pandas as pd

class H2H:
  def __init__(self, club1, club2, matches_results, matches_statistics, goals_df, both_sides= True):
    self.club1 = club1
    self.club2 = club2
    q1 = f"(`home_team`== '{club1}') and (`away_team` == '{club2}')"
    q2 = f"(`home_team`== '{club2}') and (`away_team` == '{club1}')"
    self.h2h_results = matches_results.query(f"{q1} or {q2}")
    self.x = self.h2h_results.merge(goals_df, on="id", how="left") \
                             .merge(matches_statistics, on="id", how="left")
    self.ret = {"variable": [], club1: [], club2: []}

  def adjust_column(self, df, column_name, club1, club2):
    df1 = df.query(f"home_team=='{club1}'")[[f"home_{column_name}", f"away_{column_name}"]]\
          .rename(columns={f"home_{column_name}": f"{column_name}1", f"away_{column_name}": f"{column_name}2"})
    df2 = df.query(f"away_team=='{club1}'")[[f"home_{column_name}", f"away_{column_name}"]]\
          .rename(columns={f"away_{column_name}": f"{column_name}1", f"home_{column_name}": f"{column_name}2"})
    adjusted_df = pd.concat([df1, df2])
    return adjusted_df

  def nbr_confrontation(self):
    self.ret["variable"].append("confrontations")
    nbr_confrontation = self.h2h_results["id"].count()
    self.ret[self.club1].append(nbr_confrontation)
    self.ret[self.club2].append(nbr_confrontation)

  def win_times(self):
    self.ret["variable"].append("wins")
    y = self.h2h_results.groupby("winner")["id"].count().rename("wins_times").reset_index()
    draw_times = y.query(f"winner=='draw'")["wins_times"].iloc[0]
    self.ret["variable"].append("draw")
    for club in [self.club1, self.club2]:
      self.ret[club].append(y.query(f"winner=='{club}'")["wins_times"].iloc[0])
      self.ret[club].append(draw_times)

  def scored_goals(self):
    self.ret["variable"].append("goals scored")
    for club in [self.club1, self.club2]:
      self.ret[club].append(
      self.h2h_results.query(f"home_team == '{club}'")["home_score"].sum()
      + self.h2h_results.query(f"away_team == '{club}'")["away_score"].sum()
      )

  def goal_x_match(self):
    self.ret["variable"].append("goal per match")
    nbr_confrontation = self.h2h_results["id"].count()
    self.ret[self.club1].append(round(self.ret[self.club1][-1] / nbr_confrontation, 2))
    self.ret[self.club2].append(round(self.ret[self.club2][-1] / nbr_confrontation, 2))

  def biggest_win(self):
    self.ret["variable"].append("biggest win")
    for club in [self.club1, self.club2]:
      wins = self.h2h_results.query(f"winner=='{club}'")
      home_wins = wins.query(f"home_team=='{club}'")[["home_score", "away_score"]]\
            .rename(columns={"home_score": "win_score", "away_score": "lose_score"})
      away_wins = wins.query(f"away_team=='{club}'")[["home_score", "away_score"]]\
            .rename(columns={"away_score": "win_score", "home_score": "lose_score"})
      win_scores = pd.concat([home_wins, away_wins]) \
                     .sort_values(by=["win_score", "lose_score"], ascending=[False, True])
      biggest_win = win_scores.iloc[0,:].values
      self.ret[club].append("{}-{}".format(biggest_win[0], biggest_win[1]))

  def players_with_most_goals(self):
    self.ret["variable"].append("best goal scorer")
    for club in [self.club1, self.club2]:
      q1 = f"((home_team == '{club}') and (isHome == True))"
      q2 = f"((away_team=='{club}') and (isHome == False))"
      club_goals = self.x.query(f"{q1} or {q2}")
      scorers = club_goals.groupby("player.name")["id"] \
                 .count() \
                 .rename("goals scored") \
                 .reset_index()
      max_scored_goals = scorers["goals scored"].max()
      top_goal_scorers = scorers.query("`goals scored`==@max_scored_goals")["player.name"]
      self.ret[club].append((
          " and ".join(top_goal_scorers.tolist())
          + f" with {max_scored_goals} goals"
      ))

  def average_possession(self):
    adjusted_x = self.adjust_column(self.x, "possession", self.club1, self.club2)
    self.ret["variable"].append("average possession")
    self.ret[self.club1].append(round(adjusted_x["possession1"].mean(), 2))
    self.ret[self.club2].append(round(adjusted_x["possession2"].mean(), 2))

  def average_shots_ot(self):
    adjusted_x = self.adjust_column(self.x, "shots_on_target", self.club1, self.club2)
    self.ret["variable"].append("average shots on target")
    self.ret[self.club1].append(round(adjusted_x["shots_on_target1"].mean(), 2))
    self.ret[self.club2].append(round(adjusted_x["shots_on_target2"].mean(), 2))

  def __call__(self):
    self.nbr_confrontation()
    self.win_times()
    self.scored_goals()
    self.goal_x_match()
    self.biggest_win()
    self.players_with_most_goals()
    self.average_possession()
    self.average_shots_ot()
    return pd.DataFrame(self.ret)
