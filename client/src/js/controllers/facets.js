'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:FacetsCtrl
 * @description
 * # FacetsCtrl
 * Controller of the svenClientApp facets. Loaded on startup, refresh when corpus change.
 */
angular.module('sven')
  .controller('FacetsCtrl', function ($scope, $log, CorpusFacetsFactory) {
    $log.debug('FacetsCtrl ready');
    // global facets
    $scope.facets = {};

    // load the basic facets for the given corpus. Must wait for courpus to be set indeed.
    $scope.loadAvailableFacets = function () {
    	$log.info('FacetsCtrl --> loadAvailableFacets ...');
    	CorpusFacetsFactory.query({id: $scope.corpus.id}, function(data) {
    		$log.info('FacetsCtrl --> loadAvailableFacets --> ', data.objects); // will contain timeline and tags available
    		$scope.facets = data.objects;
        $scope.ctxtimeline = data.objects.timeline;
    	});
    };

    $scope.loadFilteredFacets = function () {

    };

    $scope.$on(CORPUS_CHANGED, function() {
    	$log.info('FacetsCtrl @CORPUS_CHANGED', $scope.corpus.name);
    	$scope.loadAvailableFacets();
   	});

   	$scope.$on(API_PARAMS_CHANGED, function(){
    	$log.info('FacetsCtrl @API_PARAMS_CHANGED', $scope.corpus.name);
    	$scope.loadFilteredFacets();
   	});

    // every time that the corpus is changed, do the sync.
   	
  });