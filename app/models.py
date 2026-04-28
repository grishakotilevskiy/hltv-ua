from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MatchFormat(Base):
    __tablename__ = "match_formats"
    id   = Column(Integer, primary_key=True)
    name = Column(String(10), nullable=False)


class MatchStatus(Base):
    __tablename__ = "match_statuses"
    id   = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)


class TournamentTier(Base):
    __tablename__ = "tournament_tiers"
    id   = Column(Integer, primary_key=True)
    name = Column(String(10), nullable=False)


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    username      = Column(String(50), nullable=False, unique=True)
    email         = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_blocked    = Column(Boolean, nullable=False, default=False)

    favorites = relationship("UserFavorite", back_populates="user")


class Team(Base):
    __tablename__ = "teams"
    id           = Column(Integer, primary_key=True)
    name         = Column(String(100), nullable=False)
    logo_url     = Column(String(255))
    world_rank   = Column(Integer)
    win_rate     = Column(Numeric(5, 2))
    hltv_team_id = Column(Integer, unique=True)
    updated_at   = Column(DateTime, server_default=func.now())

    players          = relationship("Player", back_populates="team")
    favorites        = relationship("UserFavorite", back_populates="team")
    tournament_teams = relationship("TournamentTeam", back_populates="team")
    news_teams       = relationship("NewsTeam", back_populates="team")


class Tournament(Base):
    __tablename__ = "tournaments"
    id                 = Column(Integer, primary_key=True)
    tier_id            = Column(Integer, ForeignKey("tournament_tiers.id"))
    status_id          = Column(Integer, ForeignKey("match_statuses.id"))
    name               = Column(String(150), nullable=False)
    logo_url           = Column(String(255))
    start_date         = Column(Date)
    end_date           = Column(Date)
    hltv_tournament_id = Column(Integer, unique=True)

    tier             = relationship("TournamentTier")
    status           = relationship("MatchStatus")
    matches          = relationship("Match", back_populates="tournament")
    tournament_teams = relationship("TournamentTeam", back_populates="tournament")


class Match(Base):
    __tablename__ = "matches"
    id            = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    team1_id      = Column(Integer, ForeignKey("teams.id"))
    team2_id      = Column(Integer, ForeignKey("teams.id"))
    format_id     = Column(Integer, ForeignKey("match_formats.id"))
    status_id     = Column(Integer, ForeignKey("match_statuses.id"))
    start_time    = Column(DateTime)
    end_time      = Column(DateTime)
    team1_score   = Column(Integer, default=0)
    team2_score   = Column(Integer, default=0)
    hltv_match_id = Column(Integer, unique=True)

    tournament = relationship("Tournament", back_populates="matches")
    team1      = relationship("Team", foreign_keys=[team1_id])
    team2      = relationship("Team", foreign_keys=[team2_id])
    fmt        = relationship("MatchFormat")
    status     = relationship("MatchStatus")


class Player(Base):
    __tablename__ = "players"
    id             = Column(Integer, primary_key=True)
    team_id        = Column(Integer, ForeignKey("teams.id"))
    nickname       = Column(String(50), nullable=False)
    full_name      = Column(String(100))
    logo_url       = Column(String(255))
    rating_3_0     = Column(Numeric(4, 3))
    kd_ratio       = Column(Numeric(4, 3))
    headshot_pct   = Column(Numeric(5, 2))
    hltv_player_id = Column(Integer, unique=True)
    updated_at     = Column(DateTime, server_default=func.now())

    team        = relationship("Team", back_populates="players")
    news_players = relationship("NewsPlayer", back_populates="player")


class News(Base):
    __tablename__ = "news"
    id           = Column(Integer, primary_key=True)
    title        = Column(String(255), nullable=False)
    content      = Column(Text)
    published_at = Column(DateTime, server_default=func.now())

    news_teams   = relationship("NewsTeam", back_populates="news")
    news_players = relationship("NewsPlayer", back_populates="news")


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="favorites")
    team = relationship("Team", back_populates="favorites")


class TournamentTeam(Base):
    __tablename__ = "tournament_teams"
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), primary_key=True)
    team_id       = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)

    tournament = relationship("Tournament", back_populates="tournament_teams")
    team       = relationship("Team", back_populates="tournament_teams")


class NewsTeam(Base):
    __tablename__ = "news_teams"
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)

    news = relationship("News", back_populates="news_teams")
    team = relationship("Team", back_populates="news_teams")


class NewsPlayer(Base):
    __tablename__ = "news_players"
    news_id   = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True)

    news   = relationship("News", back_populates="news_players")
    player = relationship("Player", back_populates="news_players")
