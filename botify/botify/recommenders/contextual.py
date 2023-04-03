from .random import Random
from .recommender import Recommender
import random


class Contextual(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, catalog):
        self.tracks_redis = tracks_redis
        self.fallback = Random(tracks_redis)
        self.catalog = catalog

    # TODO Seminar 5 step 1: Implement contextual recommender based on NN predictions
    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = previous_track.recommendations
        if recommendations is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        shuffled = list(recommendations)
        random.shuffle(shuffled)
        return shuffled[0]

class ContextualUpdate(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, listened_redis, catalog):
        self.tracks_redis = tracks_redis
        self.listened_redis = listened_redis
        self.fallback = Random(tracks_redis)
        self.catalog = catalog

    # TODO Seminar 5 step 1: Implement contextual recommender based on NN predictions
    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        # Запрашиваем список прослушанных треков
        listened = self.listened_redis.get(user)
        if listened is not None:
            listened = list(self.catalog.from_bytes(listened))
        else:
            listened = []

        # Если предыдущий трек не понравился, ищем трек для рекомендаций из уже прослушанных
        if prev_track_time < 0.7 and prev_track_time >= 0:
            random.shuffle(listened)
            prev_track = listened[0]

        # Получаем рекомендации для трека
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = previous_track.recommendations
        if recommendations is None or len(recommendations) == 0:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        # recommendation_track = None
        not_recommended_tracks = []
        # Выбираем трек из рекомендаций, который пользователь еще не слушал
        for track in recommendations:
            if track in listened:
                continue

            not_recommended_tracks.append(track)

        if len(not_recommended_tracks) == 0:
            # Если нет тех треков, которые еще не рекомендовали. Рекомендуем рандом
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        recommendation_track = not_recommended_tracks[0]
        not_recommended_tracks.pop(0)

        listened.append(recommendation_track)

        # Обновление истории рекомендаций пользователя
        self.listened_redis.set(
            user, self.catalog.to_bytes(listened)
        )
        return recommendation_track