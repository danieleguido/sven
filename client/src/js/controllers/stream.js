'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:NetworkCtrl
 * @description
 * # NetworkCtrl
 * Controller of the svenClientApp
 */
angular.module('sven')
  .controller('StreamCtrl', function ($scope, $log, $routeParams, CorpusVisFactory, concepts) {
    $log.debug('StreamCtrl ready', concepts);
    // $scope.graph = graph
    $scope.concepts = concepts.objects;

    $scope.$on(API_PARAMS_CHANGED, function(){
      $log.info('StreamCtrl @API_PARAMS_CHANGED', $scope.getParams());
      CorpusVisFactory.get(angular.extend({
        id: $routeParams.id,
        vis:   'stream',
        model: 'concept'
      }, $scope.getParams()), function (res) {
        $scope.concepts = res.objects;
      })
    });

  })