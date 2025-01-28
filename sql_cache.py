"""
File name: sql_cache.py
Author: Luigi Saetta
Date last modified: 2024-12-02
Python Version: 3.11

Description:
    This file provide a class to handle a cache with all the requests
    more frequently made, in NL, and the resulting SQL code


Inspired by:
   

Usage:
    Import this module into other scripts to use its functions. 
    Example:


License:
    This code is released under the MIT License.

Notes:
    This is a part of a set of demos showing how to build a SQL Agent
    for Text2SQL taks

Warnings:
    This module is in development, may change in future versions.
"""

import os
import hashlib
from collections import defaultdict
import numpy as np

from langchain_community.embeddings import OCIGenAIEmbeddings
from config_reader import ConfigReader
from utils import get_console_logger

from config_private import COMPARTMENT_OCID

current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.toml")
config = ConfigReader(config_path)
logger = get_console_logger()

VERBOSE = bool(config.find_key("verbose"))


class SQLCache:
    """
    New class to manage the request cache with SQL generated

    modified to be a singleton
    """

    _instance = None  # Attributo di classe per memorizzare l'istanza unica

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Se non esiste un'istanza, creane una
            cls._instance = super(SQLCache, cls).__new__(cls)
        return cls._instance

    def __init__(self, max_size=1000):
        # Dictionary to store hash(NL) -> SQL (empty if SQL generation failed)
        self.cache = {}
        # Dictionary to store hash(NL) -> user request text
        self.user_requests = {}
        # Dictionary to store hash(NL) -> generation time in seconds
        self.generation_times = {}
        # to store embedding (added 01/11/2024)
        self.embedding = {}
        # Access count for each hash(NL)
        self.access_count = defaultdict(int)
        # Maximum cache size
        self.max_size = max_size

        auth_type = config.find_key("auth_type")
        embed_model = config.find_key("embed_model")
        embed_endpoint = config.find_key("embed_endpoint")

        # the embedding model for similarity search
        self.embed_model = OCIGenAIEmbeddings(
            auth_type=auth_type,
            model_id=embed_model,
            service_endpoint=embed_endpoint,
            compartment_id=COMPARTMENT_OCID,
        )

    def _hash_request(self, nl_request):
        """Generates a hash for the NL request."""
        return hashlib.md5(nl_request.encode()).hexdigest()

    def _get_embedding(self, request: str) -> np.ndarray:
        """Ottiene o calcola l'embedding per una richiesta."""
        return self.embed_model.embed_query(request)

    def get(self, nl_request):
        """Retrieves the SQL from the cache for a given NL request, if it exists."""
        nl_hash = self._hash_request(nl_request)
        if nl_hash in self.cache:
            # Increment the access count
            self.access_count[nl_hash] += 1
            return self.cache[nl_hash], self.embedding[nl_hash]

        # here: not found
        return None, None  # No result in cache

    def set(self, nl_request, sql_query=None, generation_time=None):
        """
        Adds a new entry hash(NL) -> SQL to the cache or updates an existing one.
        If sql_query is None, it means SQL generation failed.
        generation_time should be the time taken to generate the SQL in seconds.

        embedding is not exposed since it is for ineternal working
        """
        nl_hash = self._hash_request(nl_request)
        if nl_hash in self.cache:
            # If already present, update only if SQL was successfully generated
            if sql_query is not None:
                self.cache[nl_hash] = sql_query
                self.generation_times[nl_hash] = generation_time
                # generated internally
                self.embedding[nl_hash] = self._get_embedding(nl_request)

            self.access_count[nl_hash] += 1
        else:
            # Add new entry and set access count to 1
            self.cache[nl_hash] = sql_query  # Can be None if SQL generation failed
            # Store the original user request text
            self.user_requests[nl_hash] = nl_request

            self.generation_times[nl_hash] = generation_time
            # generated internally
            self.embedding[nl_hash] = self._get_embedding(nl_request)
            self.access_count[nl_hash] = 1
            self._maintain_size()  # Keep cache size within limit

    def _remove_entry(self, nl_hash: str):
        """Rimuove un entry dalla cache e dagli attributi collegati."""
        del self.cache[nl_hash]
        del self.access_count[nl_hash]
        del self.user_requests[nl_hash]
        del self.generation_times[nl_hash]
        del self.embedding[nl_hash]

    def _maintain_size(self):
        """Keeps the cache within the max_size limit."""
        if len(self.cache) > self.max_size:
            # Sort entries by access count in ascending order
            sorted_entries = sorted(self.access_count.items(), key=lambda item: item[1])
            # Determine number of entries to remove
            entries_to_remove = len(self.cache) - self.max_size
            for i in range(entries_to_remove):
                self._remove_entry(sorted_entries[i][0])

    def get_failed_requests(self):
        """
        Returns a list of user requests for which SQL generation failed
        (SQL is None).
        """
        return [
            self.user_requests[nl_hash]
            for nl_hash, sql in self.cache.items()
            if sql is None
        ]

    def get_stats(self):
        """Returns statistics for each cache entry as a list of dictionaries with hash,
        user request, SQL, access counts, and generation time in seconds."""
        stats = []
        for nl_hash, sql_query in self.cache.items():
            stats.append(
                {
                    # removed hash
                    "user_request": self.user_requests[nl_hash],
                    "SQL": sql_query,
                    "count": self.access_count[nl_hash],
                    "generation_time": self.generation_times.get(
                        nl_hash
                    ),  # Might be None if SQL generation failed
                }
            )
        return stats

    def __len__(self):
        """Returns the number of entries currently in cache."""
        return len(self.cache)

    def find_closer(self, request2):
        """
        Implement the similarity search in the cache (in memory)

        find the entry in cache with shorter distance from request2
        """
        request_candidate = None
        sql_candidate = None
        min_distance = float("inf")

        # out of loop
        _embedding2 = np.array(self._get_embedding(request2))

        for _hash, request in self.user_requests.items():
            # _hash is the hash of NL request
            sql = self.cache[_hash]
            _embedding1 = np.array(self.embedding[_hash])

            # we're using cosine distance
            distance = 1.0 - np.dot(_embedding1, _embedding2)

            # if we find a shorter distance we update candidate
            if distance <= min_distance:
                min_distance = distance
                request_candidate = request
                sql_candidate = sql

        # request_candidate can be None
        return request_candidate, sql_candidate, min_distance

    def find_closer_with_threshold(self, request2, threshold):
        """
        find the closer using embeddings, check the distance and compare with threshold
        """
        request_candidate, sql_candidate, min_distance = self.find_closer(request2)

        if VERBOSE:
            logger.info("")
            logger.info(
                "Closer in cache: %s, distance: %5.3f", request_candidate, min_distance
            )

        if min_distance <= threshold:
            # found in cache
            logger.info("Found in cache...")
            return sql_candidate

        # not found
        return None
