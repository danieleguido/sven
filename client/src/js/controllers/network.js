'use strict';

/**
 * @ngdoc function
 * @name svenClientApp.controller:NetworkCtrl
 * @description
 * # NetworkCtrl
 * Controller of the svenClientApp
 */
angular.module('sven')
  .controller('NetworkCtrl', function ($scope, $log, $routeParams, graph) {
    $log.debug('NetworkCtrl ready', graph);
    // map links
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
    $scope.graph = graph
  })