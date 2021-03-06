'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:NetworkCtrl
 * @description
 * # NetworkCtrl
 * Controller of the svenClientApp
 */
angular.module('sven')
  .controller('NetworkCtrl', function ($scope, $log, $routeParams, $location, graph, CorpusVisFactory) {
    $log.debug('NetworkCtrl ready', $routeParams);

    $scope.measure = 'tf';
    // watchers
    $scope.$watch('between', function (between, previous) {
      
      if(between == previous)
        return;
      if(between == 'document' || between == 'concept' || between == 'tag') {
        $location.search('between', between);
        $log.info('NetworkCtrl @between - value:', between);
      }
    });

    $scope.$on(API_PARAMS_CHANGED, function(){
      $log.info('NetworkCtrl @API_PARAMS_CHANGED', $routeParams.between, $scope.getParams());
      var between = $routeParams.between || 'concept';
      if(['document', 'concept', 'tag'].indexOf(between) == -1) {
        return;
      }
      $scope.freeze = 'sigma';
      
      CorpusVisFactory.get(angular.extend({
        id: $routeParams.id,
        vis:   'network',
        model: between
      }, $scope.getParams()), function (graph) {
        $scope.sync(graph);
      })
    });

    // map links
    $scope.sync = function(graph) {
      var c = 0
      graph.edges = graph.edges.filter(function(d) {
        return d.weight > 0
      }).map(function (d) {
        c++;
        d.id = d.id || c;
        d.source = isNaN(d.source)? d.source : graph.nodes[d.source].id
        d.target = isNaN(d.target)? d.target : graph.nodes[d.target].id
        return d
      })
      $scope.graph = graph;

      $scope.freeze = 'none';
    };

    $scope.sync(graph);
    

    $scope.between = $routeParams.between || 'concept';
    $scope.measure = $routeParams.measure || 'tf';
  })